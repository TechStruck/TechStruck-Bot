from discord.ext import commands
from discord import Embed, Color, NotFound


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

    @bot.command(aliases=["re"])
    async def redo(ctx: commands.Context):
        """Reply to a message to rerun it if its a command, helps when you've made typos"""
        ref = ctx.message.reference
        if not ref:
            return
        try:
            message = await ctx.channel.fetch_message(ref.message_id)
        except NotFound:
            return await ctx.reply("Couldn't find that message")
        await bot.process_commands(message)
