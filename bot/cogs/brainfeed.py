import asyncio
from datetime import datetime
from functools import cached_property

from discord import Embed, Member, NotFound, Reaction, TextChannel
from discord.ext import commands, flags

from bot.bot import TechStruckBot
from bot.utils.embed_flag_input import dict_to_embed, embed_input


class BrainFeed(commands.Cog):
    """BrainFeed related commands"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot
        self.submission_channel_id = 824887130853474304

    @flags.group(aliases=["bf", "brain", "feed"], invoke_without_command=True)
    async def brainfeed(self, ctx: commands.Context):
        await ctx.send_help(self.brainfeed)  # type: ignore

    @cached_property
    def submission_channel(self) -> TextChannel:
        return self.bot.get_channel(self.submission_channel_id)  # type: ignore

    @embed_input(basic=True, image=True)
    @brainfeed.command(cls=flags.FlagCommand)
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def add(self, ctx: commands.Context, **kwargs):
        embed = dict_to_embed(kwargs)
        embed.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url))
        embed.timestamp = datetime.now()
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("\u2705")
        await msg.add_reaction("\u274c")

        def check(r: Reaction, u: Member):
            return (
                u == ctx.author and r.emoji in ("\u2705", "\u274c") and r.message == msg
            )

        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check, timeout=120)
        except asyncio.TimeoutError:
            return await msg.reply("Timeout!")
        if r.emoji == "\u274c":
            return await ctx.send("Cancelled!")
        await ctx.trigger_typing()
        submission = await self.submission_channel.send(embed=embed)
        metaembed = Embed(
            title="Submission details",
            description=(
                "```"
                f"User ID: {ctx.author.id}\n"
                f"User name: {ctx.author}\n"
                f"Channel ID: {ctx.channel.id}\n"
                f"Channel name: {ctx.channel}\n"
                f"Guild ID: {ctx.guild.id}\n"
                f"Guild name: {ctx.guild}\n"
                "```"
            ),
        )
        await submission.reply(embed=metaembed)
        await ctx.send(f"Submitted\nSubmission ID: {submission.id}")

    @brainfeed.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def view(self, ctx: commands.Context, id: int):
        try:
            msg = await self.submission_channel.fetch_message(id)
        except NotFound:
            return await ctx.send("Unknown brainfeed")

        if not msg.embeds:
            return await ctx.send("Unknown brainfeed")
        embed = msg.embeds[0]
        await ctx.send(embed=embed)

    @brainfeed.command(hidden=True)
    async def approve(self, ctx: commands.Context, *, id: int):
        try:
            msg = await self.submission_channel.fetch_message(id)
        except NotFound:
            await ctx.send("Submission not found")
        else:
            await msg.remove_reaction("\u274c", ctx.guild.me)
            await msg.add_reaction("\u2705")
            await ctx.send("Approved")

    @brainfeed.command(hidden=True)
    async def deny(self, ctx: commands.Context, *, id: int):
        try:
            msg = await self.submission_channel.fetch_message(id)
        except NotFound:
            await ctx.send("Submission not found")
        else:
            await msg.remove_reaction("\u2705", ctx.guild.me)
            await msg.add_reaction("\u274c")
            await ctx.send("Denied")


def setup(bot: TechStruckBot):
    bot.add_cog(BrainFeed(bot))
