import datetime
import re
from io import BytesIO
from typing import Optional
from urllib.parse import urlencode

from cachetools import TTLCache
from discord import Color, Embed, File, Forbidden, Member
from discord.ext import commands
from jose import jwt
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from bot.utils.process_files import process_files
from config.common import config
from config.oauth import github_oauth_config
from models import UserModel


class GithubNotLinkedError(commands.CommandError):
    def __str__(self):
        return "Your github account hasn't been linked yet, please use the `linkgithub` command to do it"


class InvalidTheme(commands.CommandError):
    def __str__(self):
        return "Not a valid theme. List of all valid themes:- default, dark, radical, merko, gruvbox, tokyonight, onedark, cobalt, synthwave, highcontrast, dracula"


class Github(commands.Cog):
    """Commands related to Github"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.themes = "default dark radical merko gruvbox tokyonight onedark cobalt synthwave highcontrast dracula".split()
        self.files_regex = re.compile(r"\s{0,}```\w{0,}\s{0,}")
        self.token_cache = TTLCache(maxsize=1000, ttl=600)

    @property
    def session(self):
        return self.bot.http._HTTPClient__session  # type: ignore

    async def cog_before_invoke(self, ctx: commands.Context):
        if ctx.command == self.link_github:
            return

        token = self.token_cache.get(ctx.author.id)
        if not token:
            user = await UserModel.get_or_none(id=ctx.author.id)
            if user is None or user.github_oauth_token is None:
                raise GithubNotLinkedError()
            token = user.github_oauth_token
            self.token_cache[ctx.author.id] = token
        ctx.gh_token = token  # type: ignore

    @commands.command(name="linkgithub", aliases=["lngithub"])
    async def link_github(self, ctx: commands.Context):
        """Link your Github account through OAuth2 to gain access to Github related commands"""
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
        try:
            await ctx.author.send(
                embed=Embed(
                    title="Connect Github",
                    description=f"Click [this]({url}) to link your github account. This link invalidates in 2 minutes",
                )
            )
        except Forbidden:
            await ctx.send(
                "Your DMs are closed. Open them so I can send you the authorization link."
            )

    @commands.group(name="gist", aliases=["gs"], invoke_without_command=True)
    async def gist(self, ctx: commands.Context):
        """Commands related to Github gists"""
        await ctx.send_help(self.gist)

    @gist.command(name="create", aliases=["cr"])
    async def create_gist(self, ctx: commands.Context, *, inp: Optional[str] = None):
        """
        Create gists from within discord

        Three ways to specify the files:
        -   Reply to a message with attachments
        -   Send attachments along with the command
        -   Use a filename and codeblock... format

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

        files, skipped = await process_files(ctx, inp)

        req = await self.github_request(ctx, "POST", "/gists", json={"files": files})

        res = await req.json()
        # TODO: Make this more verbose to the user and log errors
        embed = Embed(
            title="Gist creation",
            description=res.get("html_url", "Something went wrong."),
        )
        embed.add_field(name="Files", value="\n".join(files.keys()), inline=False)
        if skipped:
            embed.add_field(
                name="Skipped files", value="\n".join(skipped), inline=False
            )
        await ctx.send(embed=embed)

    @gist.command(name="list", aliases=["ls"])
    async def list_gist(self, ctx: commands.Context):
        """
        List 10 gists made by you
        """
        req = await self.github_request(ctx, "GET", "/gists")

        gists = (await req.json())[:10]
        embed = Embed(title="Your gists", color=Color.green())
        description = "\n\n".join(
            [
                "`{0[id]}`\n[{name}]({0[html_url]})".format(
                    gist, name=next(iter(gist["files"]))
                )
                for gist in gists
            ]
        )
        embed.description = description
        await ctx.send(embed=embed)

    @gist.command("delete", aliases=["del", "rm", "remove"])
    async def delete_gist(self, ctx: commands.Context, *, gist_id: str):
        """
        Delete a gist using its ID
        You can get the ID from the list
        """
        req = await self.github_request(ctx, "DELETE", "/gists/{}".format(gist_id))
        if req.status == 204:
            return await ctx.send("Deleted")
        if req.status == 404:
            return await ctx.send("Not found")
        if req.status == 403:
            return await ctx.send("Forbidden")

    @commands.command(name="githubsearch", aliases=["ghsearch", "ghse"])
    async def github_search(self, ctx: commands.Context, *, term: str):
        """
        Search through all public repositories in Github

        Github search filters work here
        eg `ghse user:FalseDev`
        """
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
    async def github_stats(
        self, ctx: commands.Context, username: str = None, theme="radical"
    ):
        """View statistics about you/any Github user in various themes"""
        theme = self.process_theme(theme)

        url = "https://github-readme-stats.codestackr.vercel.app/api"

        username = username or await self.get_gh_user(ctx)

        file = await self.get_file_from_svg_url(
            url,
            params={
                "username": username,
                "show_icons": "true",
                "hide_border": "true",
                "theme": theme,
            },
            exclude=[b"A++", b"A+"],
        )
        await ctx.send(file=File(file, filename="stats.png"))

    @commands.command(name="githublanguages", aliases=["ghlangs", "ghtoplangs"])
    async def github_top_languages(
        self, ctx: commands.Context, username: str = None, theme: str = "radical"
    ):
        """View language usage statistics for you/any github user in various themes"""

        username = username or await self.get_gh_user(ctx)
        theme = self.process_theme(theme)
        url = "https://github-readme-stats.codestackr.vercel.app/api/top-langs/"

        file = await self.get_file_from_svg_url(
            url, params={"username": username, "theme": theme}
        )
        await ctx.send(file=File(file, filename="langs.png"))

    async def get_file_from_svg_url(
        self, url: str, *, params={}, exclude=[], fmt="PNG"
    ):
        res = await (await self.session.get(url, params=params)).content.read()
        for i in exclude:
            res = res.replace(
                i, b""
            )  # removes everything that needs to be excluded (eg. the uncentered A+)
        drawing = svg2rlg(BytesIO(res))
        return BytesIO(renderPM.drawToString(drawing, fmt=fmt))

    def process_theme(self, theme):
        theme = theme.lower()
        if theme not in self.themes:
            raise InvalidTheme()
        return theme

    @staticmethod
    def repo_desc_format(result):
        description = result["description"]
        if not description:
            return ""
        return description if len(description) < 100 else f'{description[:100]}...'

    async def github_request(
        self,
        ctx: commands.Context,
        req_type: str,
        endpoint: str,
        params: dict = None,
        json: dict = None,
    ):
        return await self.session.request(
            req_type,
            f"https://api.github.com{endpoint}",
            params=params,
            json=json,
            headers={"Authorization": f"Bearer {ctx.gh_token}"},
        )

    async def get_gh_user(self, ctx: commands.Context):
        response = await (await self.github_request(ctx, "GET", "/user")).json()
        return response.get("login")


def setup(bot: commands.Bot):
    bot.add_cog(Github(bot))
