import asyncio
from datetime import datetime
from functools import cached_property

from discord import Embed, Member, NotFound, Reaction, TextChannel
from discord.ext import commands, flags  # type: ignore
from discord.utils import get

from bot.bot import TechStruckBot
from bot.utils.embed_flag_input import dict_to_embed, embed_input


class UnknownBrainfeed(commands.CommandError):
    def __str__(self) -> str:
        return "The BrainFeed with the requested ID was not found"


class BrainFeed(commands.Cog):
    """BrainFeed related commands"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot
        self.submission_channel_id = 824887130853474304

    @flags.group(aliases=["bf", "brain", "feed"], invoke_without_command=True)
    async def brainfeed(self, ctx: commands.Context):
        """BrainFeed - the daily dose of knowledge"""
        await ctx.send_help(self.brainfeed)  # type: ignore

    @cached_property
    def submission_channel(self) -> TextChannel:
        return self.bot.get_channel(self.submission_channel_id)  # type: ignore

    @embed_input(basic=True, image=True)
    @brainfeed.command(aliases=["new", "submit"], cls=flags.FlagCommand)
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def add(self, ctx: commands.Context, **kwargs):
        """Submit your brainfeed for approval and publishing"""
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

    async def get_submission(self, bf_id) -> Embed:
        try:
            msg = await self.submission_channel.fetch_message(bf_id)
        except NotFound:
            raise UnknownBrainfeed()

        if not msg.embeds:
            raise UnknownBrainfeed()

        return msg.embeds[0]

    @brainfeed.command(aliases=["show"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def view(self, ctx: commands.Context, id: int):
        """View a BrainFeed"""
        embed = await self.get_submission(id)
        await ctx.send(embed=embed)

    @flags.add_flag("--in", "-i", type=TextChannel, default=None)
    @flags.add_flag("--webhook", "-wh", action="store_true", default=False)
    @flags.add_flag("--webhook-name", "-wn", default="BrainFeed")
    @flags.add_flag("--webhook-dispose", "-wd", action="store_true", default=False)
    @brainfeed.command(aliases=["post"], cls=flags.FlagCommand)
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True, embed_links=True)
    async def send(self, ctx: commands.Context, bf_id: int, **kwargs):
        """Publish a BrainFeed in your server"""
        channel: TextChannel = ctx.channel  # type: ignore
        if (in_ := kwargs.pop("in")) :
            channel = await in_

        embed = await self.get_submission(bf_id)

        if not kwargs.pop("webhook"):
            return await channel.send(embed=embed)

        wh_name: str = kwargs.pop("webhook_name")

        webhook = get(
            await channel.webhooks(), name=wh_name
        ) or await channel.create_webhook(name=wh_name)

        await webhook.send(embed=embed)
        if kwargs.pop("webhook_dispose"):
            await webhook.delete()

    @brainfeed.command(hidden=True)
    @commands.is_owner()
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
    @commands.is_owner()
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
