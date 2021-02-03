import re
import datetime
from urllib.parse import urlencode

from discord.ext import commands
from discord import Member, Embed
from jose import jwt

from models import UserModel
from config.oauth import github_oauth_config
from config.common import config


class GithubNotLinkedError(commands.CommandError):
    def __str__(self):
        return "Your github account hasn't been linked yet, please use the `linkgithub` command to do it"


class Github(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.files_regex = re.compile(r"\s{0,}```\w{0,}\s{0,}")

    async def cog_check(self, ctx: commands.Context):
        user = await UserModel.get_or_none(id=ctx.author.id)
        if ctx.command != self.link_github and (user is None or user.github_oauth_token is None):
            raise GithubNotLinkedError()
        ctx.user_obj = user
        return True

    @commands.command(name="linkgithub", aliases=["lngithub"])
    async def link_github(self, ctx: commands.Context):
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
        url = "https://github.com/login/oauth/authorize?" + urlencode({
            'client_id': github_oauth_config.client_id,
            'scope': "gist",
            'redirect_uri': "https://tech-struck.vercel.app/oauth/github",
            'state': jwt.encode({'id': ctx.author.id, 'expiry': str(expiry)}, config.secret),
        })
        await ctx.author.send(embed=Embed(title="Connect Github", description=f"Click [this]({url}) to link your github account. This link invalidates in 2 minutes"))

    @commands.command(name="creategist", aliases=["crgist"])
    async def create_gist(self, ctx: commands.Context, *, inp):
        files_and_names = self.files_regex.split(inp)[:-1]
        # Dict comprehension to create the files 'object'
        files = {name:{"content": content+"\n"} for name, content in zip(files_and_names[0::2], files_and_names[1::2])}

        # No need to create a new session
        req = await self.bot.http._HTTPClient__session.post("https://api.github.com/gists", headers={"Authorization":f"Bearer {ctx.user_obj.github_oauth_token}"}, json={"files":files})

        res = await req.json()
        # TODO: Make this more verbose to the user and log errors
        await ctx.send(res.get("html_url", "Something went wrong."))


def setup(bot: commands.Bot):
    bot.add_cog(Github(bot))
