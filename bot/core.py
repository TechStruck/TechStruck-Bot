from discord.ext import commands
from discord import Embed, Color


def setup(bot: commands.Bot):
    @bot.command(aliases=["latency"])
    async def ping(ctx: commands.Context):
        """Check latency of the bot"""
        latency = str(round(bot.latency*1000, 1))
        await ctx.send(embed=Embed(title="Pong!", description=f"{latency}ms", color=Color.blue()))

    @bot.command(aliases=["statistics"])
    async def stats(ctx: commands.Context):
        """Stats of the bot"""
        users = len(bot.users)
        guilds = len(bot.guilds)

        embed = Embed(color=Color.dark_green())
        embed.add_field(name="Guilds", value=guilds)
        embed.add_field(name="Users", value=users)
        embed.set_thumbnail(url=ctx.guild.me.avatar_url)

        await ctx.send(embed=embed)
