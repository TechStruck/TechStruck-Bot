import sys
import os
import inspect

from discord import Embed, Message, TextChannel
from discord.ext import commands, flags

from bot.bot import TechStruckBot
from bot.utils.embed_flag_input import (
    allowed_mentions_input,
    dict_to_allowed_mentions,
    dict_to_embed,
    embed_input,
    process_message_mentions,
    webhook_input,
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

    @embed_input(all=True)
    @allowed_mentions_input()
    @webhook_input()
    @flags.add_flag("--channel", "--in", type=TextChannel, default=None)
    @flags.add_flag("--message", "--msg", "-m", default=None)
    @flags.add_flag("--edit", "-e", type=Message, default=None)
    @flags.command(
        brief="Send an embed with any fields, in any channel, with command line like arguments"
    )
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_permissions(manage_webhooks=True, embed_links=True)
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

        if kwargs.pop("webhook"):
            if edit_message := kwargs.pop("edit"):
                edit_message.close()
            username, avatar_url = kwargs.pop("webhook_username"), kwargs.pop(
                "webhook_avatar"
            )
            if kwargs.pop("webhook_auto_author"):
                username, avatar_url = (
                    username or ctx.author.display_name,
                    avatar_url or ctx.author.avatar_url,
                )
            target = kwargs.pop("channel") or ctx.channel
            if name := kwargs.pop("webhook_new_name"):
                wh = await target.create_webhook(name=name)
            elif name := kwargs.pop("webhook_name"):
                try:
                    wh = next(
                        filter(
                            lambda wh: wh.name.casefold() == name.casefold(),
                            await target.webhooks(),
                        )
                    )
                except StopIteration:
                    return await ctx.send(
                        "No pre existing webhook found with given name"
                    )
            else:
                return await ctx.send("No valid webhook identifiers provided")
            await wh.send(
                message,
                embed=embed,
                allowed_mentions=allowed_mentions,
                username=username,
                avatar_url=avatar_url,
            )
            if kwargs.pop("webhook_dispose"):
                await wh.delete()
            return await ctx.message.add_reaction("\u2705")

        if edit := await maybe_await(kwargs.pop("edit")):
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

    @commands.command()
    async def rawembed(self, ctx: commands.Context):
        ref = ctx.message.reference
        if not ref or not ref.message_id:
            return await ctx.send("Reply to an message with an embed")
        message = ref.cached_message or await ctx.channel.fetch_message(ref.message_id)

        if not message.embeds:
            return await ctx.send("Message had no embeds")
        em = message.embeds[0]
        description = "```" + str(em.to_dict()) + "```"
        embed = Embed(description=description)
        await ctx.reply(embed=embed)

    @commands.command()
    async def source(self, ctx: commands.Context, *, command=None):
        """Get the source code of the bot or the provided command."""
        if command is None:
            return await ctx.send(
                embed=Embed(
                    description='My source can be found [here](https://github.com/TechStruck/TechStruck-Bot)!',
                    color=0x8ADCED,
                )
            )


        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            cmd = self.bot.get_command(command)
            if cmd is None:
                return await ctx.send(
                    embed=Embed(
                        description="No such command found.",
                        color=0x8ADCED
                    )
                )

            src = cmd.callback.__code__
            module = cmd.callback.__module__
            filename = src.co_filename

        lines, firstline = inspect.getsourcelines(src)
        lines = len(lines)
        location = (
            module.replace(".", "/") + ".py"
            if module.startswith("discord")
            else os.path.relpath(filename).replace(r"\\", "/")
        )

        url = f"https://github.com/TechStruck/TechStruck-Bot/blob/main/{location}#L{firstline}-L{firstline+lines-1}"
        await ctx.send(
            embed=Embed(
                description=f"Source of {command} can be found [here]({url}).",
                color=0x8ADCED
            )
        )


def setup(bot: TechStruckBot):
    bot.add_cog(Utils(bot))


def teardown(bot: TechStruckBot):
    del sys.modules["bot.utils.embed_flag_input"]
