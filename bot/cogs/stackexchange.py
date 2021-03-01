import datetime
import json
import html
import os
from urllib.parse import urlencode
import traceback

from discord import Color, Embed, Member
from discord.ext import commands, flags, tasks
from jose import jwt
from cachetools import TTLCache

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
        ctx.stack_token = token

    @commands.command(
        name="stackrep",
        aliases=["stackreputation", "stackoverflowrep", "stackoverflowreputation"],
    )
    async def stack_reputation(self, ctx: commands.Context):
        """Check your stackoverflow reputation"""
        # TODO: Use a stackexchange filter here
        # https://api.stackexchange.com/docs/filters
        data = await self.stack_request(
            ctx,
            "GET",
            "/me",
            data={
                "site": "stackoverflow",
            },
        )
        await ctx.send(data["items"][0]["reputation"])

    @flags.add_flag("--site", type=str, default="stackoverflow")
    @flags.add_flag("term", nargs="+")
    @flags.command(name="stacksearch", aliases=["stackser"])
    async def stackexchange_search(self, ctx: commands.Context, **kwargs):
        """Search stackexchange for your question"""
        term, sitename = " ".join(kwargs["term"]), kwargs["site"]

        site = None
        for s in self.sites:
            if s["api_site_parameter"] == sitename:
                site = s
                break
        if not site:
            raise StackExchangeError(f"Invalid site {sitename} provided")

        data = await self.stack_request(
            ctx,
            "GET",
            "/search/excerpts",
            data={
                "site": sitename,
                "sort": "relevance",
                "q": term,
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

    async def stack_request(
        self,
        ctx: commands.Context,
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
        await ctx.author.send(
            embed=Embed(
                title="Connect Stackexchange",
                description=f"Click [this]({url}) to link your stackexchange account. This link invalidates in 2 minutes",
                color=Color.blue(),
            )
        )


def setup(bot: commands.Bot):
    bot.add_cog(Stackexchange(bot))
