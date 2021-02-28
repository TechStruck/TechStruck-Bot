import datetime
import re
from urllib.parse import urlencode

from discord import Color, Embed, Member
from discord.ext import commands
from jose import jwt
from cachetools import TTLCache

from config.common import config
from config.oauth import github_oauth_config
from models import UserModel

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO

class GithubNotLinkedError(commands.CommandError):
    def __str__(self):
        return "Your github account hasn't been linked yet, please use the `linkgithub` command to do it"


class Github(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.files_regex = re.compile(r"\s{0,}```\w{0,}\s{0,}")
        self.token_cache = TTLCache(maxsize=1000, ttl=600)

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    async def cog_check(self, ctx: commands.Context):
        token = self.token_cache.get(ctx.author.id)
        if not token:
            user = await UserModel.get_or_none(id=ctx.author.id)
            if ctx.command != self.link_github and (
                user is None or user.github_oauth_token is None
            ):
                raise GithubNotLinkedError()
            token = user.github_oauth_token
            self.token_cache[ctx.author.id] = token
        ctx.gh_token = token
        return True

    @commands.command(name="linkgithub", aliases=["lngithub"])
    async def link_github(self, ctx: commands.Context):
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
        url = "https://github.com/login/oauth/authorize?" + urlencode(
            {
                "client_id": github_oauth_config.client_id,
                "scope": "gist",
                "redirect_uri": "https://tech-struck.vercel.app/oauth/github",
                "state": jwt.encode(
                    {"id": ctx.author.id, "expiry": str(expiry)}, config.secret
                ),
            }
        )
        await ctx.author.send(
            embed=Embed(
                title="Connect Github",
                description=f"Click [this]({url}) to link your github account. This link invalidates in 2 minutes",
            )
        )

    @commands.command(name="creategist", aliases=["crgist"])
    async def create_gist(self, ctx: commands.Context, *, inp):
        """
        Create gists from within discord

        Example:
        filename.py
        ```
        # Codeblock with contents of filename.py
        ```

        filename2.txt
        ```
        Codeblock containing filename2.txt's contents
        ```
        """
        files_and_names = self.files_regex.split(inp)[:-1]
        # Dict comprehension to create the files 'object'
        files = {
            name: {"content": content + "\n"}
            for name, content in zip(files_and_names[0::2], files_and_names[1::2])
        }

        req = await self.github_request(ctx, "POST", "/gists", json={"files": files})

        res = await req.json()
        # TODO: Make this more verbose to the user and log errors
        await ctx.send(res.get("html_url", "Something went wrong."))

    @commands.command(name="githubsearch", aliases=["ghsearch", "ghse"])
    async def github_search(self, ctx: commands.Context, *, term: str):
        # TODO: Docs

        req = await self.github_request(
            ctx, "GET", "/search/repositories", dict(q=term, per_page=5)
        )

        data = await req.json()
        if not data["items"]:
            return await ctx.send(
                embed=Embed(
                    title=f"Searched for {term}",
                    color=Color.red(),
                    description="No results found",
                )
            )

        em = Embed(
            title=f"Searched for {term}",
            color=Color.green(),
            description="\n\n".join(
                [
                    "[{0[owner][login]}/{0[name]}]({0[html_url]})\n{0[stargazers_count]:,} :star:\u2800{0[forks_count]} \u2387\u2800\n{1}".format(
                        result, self.repo_desc_format(result)
                    )
                    for result in data["items"]
                ]
            ),
        )

        await ctx.send(embed=em)
        
        
    @commands.command(name="githubstats", aliases=["ghstats", "ghst"])
    async def github_stats(ctx,username = "codewithswastik",theme="radical"):
        theme = theme.lower()
        themes = "default dark radical merko gruvbox tokyonight onedark cobalt synthwave highcontrast dracula".split(" ")
        if theme not in themes:
            return await ctx.send("Not a valid theme. List of all valid themes:- default, dark, radical, merko, gruvbox, tokyonight, onedark, cobalt, synthwave, highcontrast, dracula")
        url = f"https://github-readme-stats.codestackr.vercel.app/api?username={username}&show_icons=true&hide_border=true&theme={theme}"
        
        
        file = await getFileFromSVGURL(url, exclude = [b"A+"])
        await ctx.send(file = discord.File(file,filename="stats.png"))
        
    @commands.command(name="githublanguages", aliases=["ghlangs", "ghtoplangs"])     
    async def github_top_languages(ctx,username = "codewithswastik",theme="radical"):
        theme = theme.lower()
        themes = "default dark radical merko gruvbox tokyonight onedark cobalt synthwave highcontrast dracula".split(" ")
        if theme not in themes:
            return await ctx.send("Not a valid theme. List of all valid themes:- default, dark, radical, merko, gruvbox, tokyonight, onedark, cobalt, synthwave, highcontrast, dracula")
        url = f"https://github-readme-stats.codestackr.vercel.app/api/top-langs/?username={username}&theme={theme}"

        file = await getFileFromSVGURL(url)
        await ctx.send(file = discord.File(file,filename="langs.png"))
 
       
    async def getFileFromSVGURL(url,exclude = [], fmt="PNG"):
        res = await (await self.session.get(url)).content.read()
        for i in exclude:
            res = res.replace(i,b"") #removes everything that needs to be excluded (eg. the uncentered A+)
        drawing = svg2rlg(BytesIO(res))
        file = BytesIO(renderPM.drawToString(drawing, fmt=fmt))
        return file
        
    @staticmethod
    def repo_desc_format(result):
        description = result["description"]
        if not description:
            return ""
        return description if len(description) < 100 else (description[:100] + "...")

    def github_request(
        self,
        ctx: commands.Context,
        req_type: str,
        endpoint: str,
        params: dict = None,
        json: dict = None,
    ):
        return self.session.request(
            req_type,
            f"https://api.github.com{endpoint}",
            params=params,
            json=json,
            headers={"Authorization": f"Bearer {ctx.gh_token}"},
        )


def setup(bot: commands.Bot):
    bot.add_cog(Github(bot))
