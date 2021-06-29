from aiohttp import ContentTypeError
from discord import Color, Embed
from discord.ext.commands import Cog, Context, command

from ..bot import TechStruckBot

class Packages(Cog):
    """Commands related to Package Search"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @property
    def session(self):
        return self.bot.session

    async def get_package(self, url: str):
        return await self.session.get(url=url)

    @command(aliases=["pypi"])
    async def pypisearch(self, ctx: Context, arg: str):
        """Get info about a Python package directly from PyPi"""

        res_raw = await self.get_package(f"https://pypi.org/pypi/{arg}/json")

        try:
            res_json = await res_raw.json()
        except ContentTypeError:
            return await ctx.send(
                embed=Embed(
                    description="No such package found in the search query.",
                    color=Color.blurple(),
                )
            )

        res = res_json["info"]

        def getval(key):
            return res[key] or "Unknown"

        name = getval("name")
        author = getval("author")
        author_email = getval("author_email")

        description = getval("summary")
        home_page = getval("home_page")

        project_url = getval("project_url")
        version = getval("version")
        _license = getval("license")

        embed = Embed(
            title=f"{name} PyPi Stats", description=description, color=Color.teal()
        )

        embed.add_field(name="Author", value=author, inline=True)
        embed.add_field(name="Author Email", value=author_email, inline=True)

        embed.add_field(name="Version", value=version, inline=False)
        embed.add_field(name="License", value=_license, inline=True)

        embed.add_field(name="Project Url", value=project_url, inline=False)
        embed.add_field(name="Home Page", value=home_page)

        embed.set_thumbnail(url="https://i.imgur.com/syDydkb.png")

        await ctx.send(embed=embed)

    @command(aliases=["npm"])
    async def npmsearch(self, ctx: Context, arg: str):
        """Get info about a NPM package directly from the NPM Registry"""

        res_raw = await self.get_package(f"https://registry.npmjs.org/{arg}/")

        res_json = await res_raw.json()

        if res_json.get("error"):
            return await ctx.send(
                embed=Embed(
                    description="No such package found in the search query.",
                    color=0xCC3534,
                )
            )

        latest_version = res_json["dist-tags"]["latest"]
        latest_info = res_json["versions"][latest_version]

        def getval(*keys):
            keys = list(keys)
            val = latest_info.get(keys.pop(0)) or {}

            if keys:
                for i in keys:
                    try:
                        val = val.get(i)
                    except TypeError:
                        return "Unknown"

            return val or "Unknown"

        pkg_name = getval("name")
        description = getval("description")

        author = getval("author", "name")
        author_email = getval("author", "email")

        repository = (
            getval("repository", "url").removeprefix("git+").removesuffix(".git")
        )

        homepage = getval("homepage")
        _license = getval("license")

        em = Embed(
            title=f"{pkg_name} NPM Stats", description=description, color=0xCC3534
        )

        em.add_field(name="Author", value=author, inline=True)
        em.add_field(name="Author Email", value=author_email, inline=True)

        em.add_field(name="Latest Version", value=latest_version, inline=False)
        em.add_field(name="License", value=_license, inline=True)

        em.add_field(name="Repository", value=repository, inline=False)
        em.add_field(name="Homepage", value=homepage, inline=True)

        em.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Npm-logo.svg/800px-Npm-logo.svg.png"
        )

        await ctx.send(embed=em)

    @command(aliases=["crates"])
    async def crate(self, ctx: Context, arg: str):
        """Get info about a Rust package directly from the Crates.IO Registry"""

        res_raw = await self.get_package(f"https://crates.io/api/v1/crates/{arg}")

        res_json = await res_raw.json()

        if res_json.get("errors"):
            return await ctx.send(
                embed=Embed(
                    description="No such package found in the search query.",
                    color=0xE03D29,
                )
            )
        main_info = res_json["crate"]
        latest_info = res_json["versions"][0]

        def getmainval(key):
            return main_info[key] or "Unknown"

        def getversionvals(*keys):
            keys = list(keys)
            val = latest_info.get(keys.pop(0)) or {}

            if keys:
                for i in keys:
                    try:
                        val = val.get(i)
                    except TypeError:
                        return "Unknown"

            return val or "Unknown"

        pkg_name = getmainval("name")
        description = getmainval("description")
        downloads = getmainval("downloads")

        publisher = getversionvals("published_by", "name")
        latest_version = getversionvals("num")
        repository = getmainval("repository")

        homepage = getmainval("homepage")
        _license = getversionvals("license")

        em = Embed(
            title=f"{pkg_name} crates.io Stats", description=description, color=0xE03D29
        )

        em.add_field(name="Published By", value=publisher, inline=True)
        em.add_field(name="Downloads", value="{:,}".format(downloads), inline=True)

        em.add_field(name="Latest Version", value=latest_version, inline=False)
        em.add_field(name="License", value=_license, inline=True)

        em.add_field(name="Repository", value=repository, inline=False)
        em.add_field(name="Homepage", value=homepage, inline=True)

        em.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Rust_programming_language_black_logo.svg/2048px-Rust_programming_language_black_logo.svg.png"
        )

        await ctx.send(embed=em)

def setup(bot: TechStruckBot):
    bot.add_cog(Packages(bot))
