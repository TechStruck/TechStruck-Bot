from discord import Embed
from discord.ext.commands import Cog, Context, command

from ..bot import TechStruckBot


class Crate(Cog):
    """Commands related to crates.io Package Search"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @property
    def session(self):
        return self.bot.session

    async def get_package(self, arg: str):
        return await self.session.get(url=f"https://crates.io/api/v1/crates/{arg}")

    @command(aliases=["crates"])
    async def crate(self, ctx: Context, arg: str):
        """Get info about a Rust package directly from the Crates.IO Registry"""

        res_raw = await self.get_package(arg)

        res_json = await res_raw.json()

        if res_json.get("errors"):
            return await ctx.send(
              embed=discord.Embed(
                  description="No such package found in the search query.", 
                  color=0xe03d29
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
            title=f"{pkg_name} crates.io Stats", description=description, color=0xe03d29
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
    bot.add_cog(NPM(bot))
