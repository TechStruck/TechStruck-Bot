import re
import sys

from discord import Message, TextChannel
from discord.ext import commands, flags

from bot.bot import TechStruckBot
from bot.utils.embed_flag_input import (
    allowed_mentions_input,
    dict_to_allowed_mentions,
    dict_to_embed,
    embed_input,
    process_message_mentions,
)

flags._converters.CONVERTERS["Message"] = commands.MessageConverter().convert


async def maybe_await(coro):
    if not coro:
        return
    return await coro


class Utils(commands.Cog):
    """Utility commands"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @embed_input
    @allowed_mentions_input
    @flags.add_flag("--channel", "--in", type=TextChannel, default=None)
    @flags.add_flag("--message", "--msg", "-m", default=None)
    @flags.add_flag("--edit", "-e", type=Message, default=None)
    @flags.command(
        brief="Send an embed with any fields, in any channel, with command line like arguments"
    )
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.bot_has_guild_permissions()
    async def embed(self, ctx: commands.Context, **kwargs):
        """
        Send an embed and its fully customizable
        Default mention settings:
            Users:      Enabled
            Roles:      Disabled
            Everyone:   Disabled
        """
        embed = dict_to_embed(kwargs, author=ctx.author)
        allowed_mentions = dict_to_allowed_mentions(kwargs)
        message = process_message_mentions(kwargs.pop("message"))

        if (edit := await maybe_await(kwargs.pop("edit"))) :
            if edit.author != ctx.guild.me:
                return await ctx.send(
                    f"The target message wasn't sent by me! It was sent by {edit.author}"
                )
            await edit.edit(
                content=message, embed=embed, allowed_mentions=allowed_mentions
            )
        else:
            target = kwargs.pop("channel") or ctx
            await target.send(message, embed=embed, allowed_mentions=allowed_mentions)
        await ctx.message.add_reaction("\u2705")


def setup(bot: TechStruckBot):
    bot.add_cog(Utils(bot))


def teardown(bot: TechStruckBot):
    del sys.modules["bot.utils.embed_flag_input"]
