import discord
from discord import Embed, Color
from discord.ext import commands
from aiohttp import ContentTypeError

class PyPi(commands.Cog):
    """Commands related to Package Search"""

    def __init__(self, bot: commands.Bot):
        
        self.bot = bot

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    async def get_package(self, arg: str):

        return await self.session.get(
            url = f"https://pypi.org/pypi/{arg}/json"
        )

    @commands.command(aliases = ['pypi', 'package', 'packageinfo'])
    async def pypisearch(self, ctx: commands.Context, arg: str):
        """Get info about a Python package direct from PyPi"""

        res_raw = await self.get_package(arg)
        
        try:
            
            res_json = await res_raw.json()
        
        except ContentTypeError:
            
            return await ctx.send(
                embed = Embed(
                    description = "No such package found in the search query.", 
                    color = Color.blurple()
                )
            )
        
        res = res_json["info"]

        name = res["name"] or "Unknown"
        author = res["author"] or "Unknown"
        author_email = res["author_email"] or "Unknown"

        description = res["summary"] or "Unknown"
        home_page = res["home_page"] or "Unknown"
        
        project_url = res["project_url"] or "Unknown"
        version = res["version"] or "Unknown"
        _license = res["license"] or "Unknown"

        embed = Embed(
            title = f"{name} PyPi Stats", 
            description = description, 
            color = Color.teal()
            )
        
        embed.add_field(name = "Author", value = author, inline = True)
        embed.add_field(name = "Author Email", value = author_email, inline = True)

        embed.add_field(name = "Version", value = version, inline = False)
        embed.add_field(name = "License", value = _license, inline = True)

        embed.add_field(name = "Project Url", value = project_url, inline = False)
        embed.add_field(name = "Home Page", value = home_page)

        embed.set_thumbnail(url = "https://i.imgur.com/syDydkb.png")

        await ctx.send(embed = embed)

def setup(bot: commands.Bot):
    bot.add_cog(PyPi(bot))
