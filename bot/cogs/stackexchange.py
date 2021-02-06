import datetime
from urllib.parse import urlencode

from discord.ext import commands
from discord import Member, Embed, Color
from jose import jwt

from models import UserModel
from config.oauth import stack_oauth_config
from config.common import config


class StackExchangeNotLinkedError(commands.CommandError):
    def __str__(self):
        return "Your stackexchange account hasn't been linked yet, please use the `linkstack` command to do it"


class Stackexchange(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base_url = "https://api.stackexchange.com/2.2"
        self.search_result_template = "[Link]({})\nViews: {}\nTags: {}"

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    async def cog_check(self, ctx: commands.Context):
        user = await UserModel.get_or_none(id=ctx.author.id)
        if ctx.command != self.link_stackoverflow and (user is None or user.stackoverflow_oauth_token is None):
            raise StackExchangeNotLinkedError()
        ctx.user_obj = user
        return True

    @commands.command(name="stackrep",
                      aliases=["stackreputation", "stackoverflowrep", "stackoverflowreputation"])
    async def stack_reputation(self, ctx: commands.Context):
        """Check your stackoverflow reputation"""
        # TODO: Use a stackexchange filter here
        # https://api.stackexchange.com/docs/filters
        res = await self.session.get(
            self.base_url + "/me",
            data={**stack_oauth_config.dict(),
                  "access_token": ctx.user_obj.stackoverflow_oauth_token,
                  "site": "stackoverflow"}
        )
        data = await res.json()
        await ctx.send(data['items'][0]['reputation'])

    @commands.command(name="stacksearch", aliases=["stackser"])
    async def stackoverflow_search(self, ctx: commands.Context, *, term: str):
        """Search stackoverflow for your error/issue"""
        res = await self.session.get(
            self.base_url + "/search/advanced",
            data={**stack_oauth_config.dict(),
                  "access_token": ctx.user_obj.stackoverflow_oauth_token,
                  "site": "stackoverflow",
                  "q": term,
                  "pagesize": 5}
        )
        data = await res.json()
        embed = Embed(title="Stackoverflow search", color=Color.green())
        if data['items']:
            for i, q in enumerate(data['items'], 1):
                tags = "\t".join(["`"+t+"`" for t in q["tags"]])
                embed.add_field(
                    name=str(i) + " " + q['title'],
                    value=self.search_result_template.format(q['link'] , q['view_count'], tags),
                    inline=False
                )
        else:
            embed.add_field(name="Oops", value="Couldn't find any results")
        await ctx.send(embed=embed)

    @commands.command(name="linkstack", aliases=["lnstack"])
    async def link_stackoverflow(self, ctx: commands.Context):
        """Link your stackoverflow account"""
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
        url = "https://stackoverflow.com/oauth/?" + urlencode({
            'client_id': stack_oauth_config.client_id,
            'scope': "no_expiry",
            'redirect_uri': "https://tech-struck.vercel.app/oauth/stackexchange",
            'state': jwt.encode({'id': ctx.author.id, 'expiry': str(expiry)}, config.secret),
        })
        await ctx.author.send(embed=Embed(title="Connect Stackexchange", description=f"Click [this]({url}) to link your stackexchange account. This link invalidates in 2 minutes", color=Color.blue()))


def setup(bot: commands.Bot):
    bot.add_cog(Stackexchange(bot))
