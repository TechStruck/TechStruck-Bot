import discord
from discord import Embed, Color
from discord.ext import commands
from aiohttp import ContentTypeError

class PyPi(commands.Cog):

    def __init__(self, bot: commands.Bot):
        
        self.bot = bot

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    async def get_package(self, arg: str):

        return await self.session.get(
            url = f"https://pypi.org/pypi/{arg}/json"
        )

    @commands.command(aliases = ['pypi', 'package'])
    async def pypisearch(self, ctx: commands.Context, arg: str):

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

        name = res["name"] or None
        author = res["author"] or None
        author_email = res["author_email"] or None

        description = res["summary"] or None
        home_page = res["home_page"] or None
        
        project_url = res["project_url"] or None
        version = res["version"] or None
        _license = res["license"] or None

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
