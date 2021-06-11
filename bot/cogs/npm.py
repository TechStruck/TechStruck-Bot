from discord import Embed
from discord.ext.commands import Cog, Context, command

from ..bot import TechStruckBot


class NPM(Cog):
    """Commands related to NPM Package Search"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @property
    def session(self):
        return self.bot.session

    async def get_package(self, arg: str):
        return await self.session.get(url=f"https://registry.npmjs.org/{arg}/")

    @command(aliases=["npm"])
    async def npmsearch(self, ctx: Context, arg: str):
        """Get info about a NPM package directly from the NPM Registry"""

        res_raw = await self.get_package(arg)

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
                    except KeyError:
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


def setup(bot: TechStruckBot):
    bot.add_cog(NPM(bot))
