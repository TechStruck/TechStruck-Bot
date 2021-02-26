from discord import Color, Embed, NotFound
from discord.ext import commands


class Common(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check latency of the bot"""
        latency = str(round(self.bot.latency*1000, 1))
        await ctx.send(embed=Embed(title="Pong!", description=f"{latency}ms", color=Color.blue()))

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx: commands.Context):
        """Stats of the bot"""
        users = len(self.bot.users)
        guilds = len(self.bot.guilds)

        embed = Embed(color=Color.dark_green())
        embed.add_field(name="Guilds", value=guilds)
        embed.add_field(name="Users", value=users)
        embed.set_thumbnail(url=ctx.guild.me.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(aliases=["re"])
    async def redo(self, ctx: commands.Context):
        """Reply to a message to rerun it if its a command, helps when you've made typos"""
        ref = ctx.message.reference
        if not ref:
            return
        try:
            message = await ctx.channel.fetch_message(ref.message_id)
        except NotFound:
            return await ctx.reply("Couldn't find that message")
        if message.author != ctx.author:
            return
        await self.bot.process_commands(message)


def setup(bot: commands.Bot):
    bot.add_cog(Common(bot))
