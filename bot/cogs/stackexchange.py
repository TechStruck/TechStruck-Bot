import datetime
import html
import json
import os
import traceback
from typing import Optional
from urllib.parse import urlencode

from cachetools import TTLCache
from discord import Color, Embed, Forbidden, Member
from discord.ext import commands, flags, tasks
from jose import jwt

from bot.utils import fuzzy
from config.common import config
from config.oauth import stack_oauth_config
from models import UserModel

search_result_template = "[View]({site[site_url]}/q/{q[question_id]})\u2800\u2800Score: {q[score]}\u2800\u2800Tags: {tags}"


class StackExchangeNotLinkedError(commands.CommandError):
    def __str__(self):
        return "Your stackexchange account hasn't been linked yet, please use the `linkstack` command to do it"


class StackExchangeError(commands.CommandError):
    pass


class Stackexchange(commands.Cog):
    """Commands related to the StackExchange network"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ready = False
        self.sites = None
        self.token_cache = TTLCache(maxsize=1000, ttl=600)
        self.load_sites.start()

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    @tasks.loop(count=1)
    async def load_sites(self):
        if os.path.isfile("cache/stackexchange_sites.json"):
            with open("cache/stackexchange_sites.json") as f:
                self.sites = json.load(f)
        else:
            try:
                data = await self.stack_request(
                    None,
                    "GET",
                    "/sites",
                    params={"pagesize": "500", "filter": "*Ids4-aWV*RW_UxCPr0D"},
                )
            except Exception:
                return traceback.print_exc()
            else:
                self.sites = data["items"]
                if not os.path.isdir("cache"):
                    os.mkdir("cache")
                with open("cache/stackexchange_sites.json", "w") as f:
                    json.dump(self.sites, f)

        self.ready = True

    async def cog_check(self, ctx: commands.Context):
        if not self.ready:
            raise StackExchangeError("Stackexchange commands are not ready yet")
        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        if ctx.command == self.link_stackoverflow:
            return

        token = self.token_cache.get(ctx.author.id)
        if not token:
            user = await UserModel.get_or_none(id=ctx.author.id)
            if user is None or user.stackoverflow_oauth_token is None:
                raise StackExchangeNotLinkedError()

            token = user.stackoverflow_oauth_token
            self.token_cache[ctx.author.id] = token
        ctx.stack_token = token  # type: ignore

    @flags.add_flag("--site", type=str, default="stackoverflow")
    @flags.command(
        name="stackprofile",
        aliases=["stackpro", "stackacc", "stackaccount"],
    )
    async def stack_profile(self, ctx: commands.Context, **kwargs):
        """Check your stackoverflow reputation"""
        # TODO: Use a stackexchange filter here
        # https://api.stackexchange.com/docs/filters
        site = self.get_site(kwargs["site"])
        data = await self.stack_request(
            ctx,
            "GET",
            "/me",
            data={
                "site": site["api_site_parameter"],
            },
        )
        if not data["items"]:
            return await ctx.send("You don't have an account in this site!")
        profile = data["items"][0]
        embed = Embed(title=site["name"] + " Profile", color=0x0077CC)

        embed.add_field(name="Username", value=profile["display_name"], inline=False)
        embed.add_field(name="Reputation", value=profile["reputation"], inline=False)
        embed.add_field(
            name="Badges",
            value="\U0001f947 {0[gold]} \u2502 \U0001f948 {0[silver]} \u2502 \U0001f949 {0[bronze]}".format(
                profile["badge_counts"]
            ),
            inline=False,
        )

        embed.set_thumbnail(url=profile["profile_image"])
        await ctx.send(embed=embed)

    @flags.add_flag("--site", type=str, default="stackoverflow")
    @flags.add_flag("--tagged", type=str, nargs="+", default=[])
    @flags.add_flag("term", nargs="+")
    @flags.command(name="stacksearch", aliases=["stackser"])
    async def stackexchange_search(self, ctx: commands.Context, **kwargs):
        """Search stackexchange for your question"""
        term, sitename, tagged = (
            " ".join(kwargs["term"]),
            kwargs["site"],
            kwargs["tagged"],
        )

        site = self.get_site(sitename)

        data = await self.stack_request(
            ctx,
            "GET",
            "/search/excerpts",
            data={
                "site": sitename,
                "sort": "relevance",
                "q": term,
                "tagged": ";".join(tagged),
                "pagesize": 5,
                "filter": "ld-5YXYGN1SK1e",
            },
        )
        embed = Embed(title=f"{site['name']} search", color=Color.green())
        embed.set_thumbnail(url=site["icon_url"])
        if data["items"]:
            for i, q in enumerate(data["items"], 1):
                tags = "\u2800".join(["`" + t + "`" for t in q["tags"]])
                embed.add_field(
                    name=str(i) + " " + html.unescape(q["title"]),
                    value=search_result_template.format(site=site, q=q, tags=tags),
                    inline=False,
                )
        else:
            embed.add_field(name="Oops", value="Couldn't find any results")
        await ctx.send(embed=embed)

    @commands.command(aliases=["stacksites"])
    async def stacksite(self, ctx: commands.Context, *, term: str):
        """Search through list of stackexchange sites and find relevant ones"""
        sites = fuzzy.finder(term, self.sites, key=lambda s: s["name"], lazy=False)[:5]  # type: ignore
        embed = Embed(color=Color.blue())
        description = "\n".join(
            ["[`{0[name]}`]({0[site_url]})".format(site) for site in sites]
        )
        embed.description = description
        await ctx.send(embed=embed)

    def get_site(self, sitename: str):
        sitename = sitename.lower()
        for site in self.sites:
            if site["api_site_parameter"] == sitename:
                return site
        raise StackExchangeError(f"Invalid site {sitename} provided")

    async def stack_request(
        self,
        ctx: Optional[commands.Context],
        method: str,
        endpoint: str,
        params: dict = {},
        data: dict = {},
    ):
        data.update(stack_oauth_config.dict())
        if ctx:
            data["access_token"] = (ctx.stack_token,)
        res = await self.session.request(
            method,
            f"https://api.stackexchange.com/2.2{endpoint}",
            params=params,
            data=data,
        )

        data = await res.json()
        if "error_message" in data:
            raise StackExchangeError(data["error_message"])
        return data

    @commands.command(name="linkstack", aliases=["lnstack"])
    async def link_stackoverflow(self, ctx: commands.Context):
        """Link your stackoverflow account"""
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
        url = "https://stackoverflow.com/oauth/?" + urlencode(
            {
                "client_id": stack_oauth_config.client_id,
                "scope": "no_expiry",
                "redirect_uri": "https://tech-struck.vercel.app/oauth/stackexchange",
                "state": jwt.encode(
                    {"id": ctx.author.id, "expiry": str(expiry)}, config.secret
                ),
            }
        )
        try:
            await ctx.author.send(
                embed=Embed(
                    title="Connect Stackexchange",
                    description=f"Click [this]({url}) to link your stackexchange account. This link invalidates in 2 minutes",
                    color=Color.blue(),
                )
            )
        except Forbidden:
            await ctx.send(
                "Your DMs (direct messages) are closed. Open them so I can send you a safe authorization link."
            )


def setup(bot: commands.Bot):
    bot.add_cog(Stackexchange(bot))
