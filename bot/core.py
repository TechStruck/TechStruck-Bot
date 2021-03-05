from discord import Color, Embed, NotFound
from discord.ext import commands

from models import GuildModel

from .bot import TechStruckBot


class Common(commands.Cog):
    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @commands.command(aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check latency of the bot"""
        latency = str(round(self.bot.latency * 1000, 1))
        await ctx.send(
            embed=Embed(title="Pong!", description=f"{latency}ms", color=Color.blue())
        )

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx: commands.Context):
        """Stats of the bot"""
        users = len(self.bot.users)
        guilds = len(self.bot.guilds)

        embed = Embed(color=Color.dark_green())
        embed.add_field(name="Guilds", value=str(guilds))
        embed.add_field(name="Users", value=str(users))
        embed.set_thumbnail(url=str(ctx.guild.me.avatar_url))

        await ctx.send(embed=embed)

    @commands.command(aliases=["re"])
    async def redo(self, ctx: commands.Context):
        """Reply to a message to rerun it if its a command, helps when you've made typos"""
        ref = ctx.message.reference
        if ref is None or ref.message_id is None:
            return
        try:
            message = await ctx.channel.fetch_message(ref.message_id)
        except NotFound:
            return await ctx.reply("Couldn't find that message")
        if message.author != ctx.author:
            return
        await self.bot.process_commands(message)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setprefix(self, ctx: commands.Context, *, prefix: str):
        """Set a custom prefix for the current server"""
        if len(prefix) > 10:
            return await ctx.send("Prefix too long, must be within 10 characters!")
        self.bot.prefix_cache[ctx.guild.id] = prefix
        await GuildModel.filter(id=ctx.guild.id).update(prefix=prefix)
        await ctx.send("My prefix has been updated to `{prefix}`")

    @commands.command()
    async def prefix(self, ctx: commands.Context):
        """View current prefix of bot"""
        await ctx.send(
            f"My prefix here is `"
            + (self.bot.prefix_cache[ctx.guild.id] if ctx.guild else ".")
            + "`"
        )


def setup(bot: TechStruckBot):
    bot.add_cog(Common(bot))
