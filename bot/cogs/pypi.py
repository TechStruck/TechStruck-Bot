from aiohttp import ContentTypeError
from discord import Color, Embed
from discord.ext.commands import Cog, Context, command

from ..bot import TechStruckBot


class PyPi(Cog):
    """Commands related to Package Search"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @property
    def session(self):
        return self.bot.session

    async def get_package(self, arg: str):
        return await self.session.get(url=f"https://pypi.org/pypi/{arg}/json")

    @command(aliases=["pypi", "package", "packageinfo"])
    async def pypisearch(self, ctx: Context, arg: str):
        """Get info about a Python package directly from PyPi"""

        res_raw = await self.get_package(arg)

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


def setup(bot: TechStruckBot):
    bot.add_cog(PyPi(bot))
