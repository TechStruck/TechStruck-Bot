import asyncio
import contextlib
import math
import re
import traceback
from typing import Iterable

from aiohttp import ClientSession
from discord import (
    AllowedMentions,
    AsyncWebhookAdapter,
    Color,
    Embed,
    Forbidden,
    Intents,
    Message,
    NotFound,
    TextChannel,
    Webhook,
    utils,
)
from discord.ext import commands, tasks
from discord.http import HTTPClient
from tortoise import Tortoise

from config.bot import bot_config
from models import GuildModel


class TechStruckBot(commands.Bot):
    http: HTTPClient

    def __init__(self, *, tortoise_config, load_extensions=True, loadjsk=True):
        allowed_mentions = AllowedMentions(
            users=True, replied_user=True, roles=False, everyone=False
        )
        super().__init__(
            command_prefix=self.get_custom_prefix,
            intents=Intents.all(),
            allowed_mentions=allowed_mentions,
            description="A bot by and for developers to integrate several tools into one place.",
            strip_after_prefix=True,
        )
        self.tortoise_config = tortoise_config
        self.db_connected = False
        self.prefix_cache = {}
        self.connect_db.start()

        if load_extensions:
            self.load_extensions(
                (
                    "bot.core",
                    "bot.cogs.admin",
                    "bot.cogs.thank",
                    "bot.cogs.stackexchange",
                    "bot.cogs.github",
                    "bot.cogs.help_command",
                    "bot.cogs.code_exec",
                    "bot.cogs.fun",
                    "bot.cogs.rtfm",
                    "bot.cogs.joke",
                    "bot.cogs.npm",
                    "bot.cogs.pypi",
                    "bot.cogs.utils",
                    "bot.cogs.brainfeed",
                    "bot.cogs.cratesio",
                )
            )
        if loadjsk:
            self.load_extension("jishaku")

    @property
    def session(self) -> ClientSession:
        return self.http._HTTPClient__session  # type: ignore

    @tasks.loop(seconds=0, count=1)
    async def connect_db(self):
        print("Connecting to db")
        await Tortoise.init(self.tortoise_config)
        self.db_connected = True
        print("Database connected")

    def load_extensions(self, extentions: Iterable[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_message(self, msg: Message):
        if msg.author.bot:
            return
        while not self.db_connected:
            await asyncio.sleep(0.2)
        user_id = self.user.id
        if msg.content in (f"<@{user_id}>", f"<@!{user_id}>"):
            return await msg.reply(
                "My prefix here is `{}`".format(await self.fetch_prefix(msg))
            )
        await self.process_commands(msg)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if not isinstance(error, commands.CommandInvokeError):
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            return await ctx.send(
                embed=Embed(title=title, description=str(error), color=Color.red())
            )

        # If we've reached here, the error wasn't expected
        # Report to logs
        embed = Embed(
            title="Error",
            description="An unknown error has occurred and my developer has been notified of it.",
            color=Color.red(),
        )
        with contextlib.suppress(NotFound, Forbidden):
            await ctx.send(embed=embed)

        traceback_text = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        length = len(traceback_text)
        chunks = math.ceil(length / 1990)

        traceback_texts = [
            traceback_text[l * 1990 : (l + 1) * 1990] for l in range(chunks)
        ]
        traceback_embeds = [
            Embed(
                title="Traceback",
                description=("```py\n" + text + "\n```"),
                color=Color.red(),
            )
            for text in traceback_texts
        ]

        # Add message content
        info_embed = Embed(
            title="Message content",
            description="```\n" + utils.escape_markdown(ctx.message.content) + "\n```",
            color=Color.red(),
        )
        # Guild information
        value = (
            (
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Joined**: {0.me.joined_at}\n"
                "**Member count**: {0.member_count}\n"
                "**Permission integer**: {0.me.guild_permissions.value}"
            ).format(ctx.guild)
            if ctx.guild
            else "None"
        )

        info_embed.add_field(name="Guild", value=value)
        # Channel information
        if isinstance(ctx.channel, TextChannel):
            value = (
                "**Type**: TextChannel\n"
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Permission integer**: {1}\n"
            ).format(ctx.channel, ctx.channel.permissions_for(ctx.guild.me).value)
        else:
            value = (
                "**Type**: DM\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
            ).format(ctx.channel)

        info_embed.add_field(name="Channel", value=value)

        # User info
        value = (
            "**Name**: {0}\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
        ).format(ctx.author)

        info_embed.add_field(name="User", value=value)

        wh = Webhook.from_url(
            bot_config.log_webhook, adapter=AsyncWebhookAdapter(self.session)
        )
        return await wh.send(embeds=[*traceback_embeds, info_embed])

    async def get_custom_prefix(self, _, message: Message) -> str:
        prefix = await self.fetch_prefix(message)
        bot_id = self.user.id
        prefixes = [prefix, f"<@{bot_id}> ", f"<@!{bot_id}> "]

        comp = re.compile(
            "^(" + "|".join(re.escape(p) for p in prefixes) + ").*", flags=re.I
        )
        match = comp.match(message.content)
        if match is not None:
            return match.group(1)
        return prefix

    async def fetch_prefix(self, message: Message) -> str:
        # DMs/Group
        if not message.guild:
            return "."

        guild_id = message.guild.id
        # Get from cache
        if guild_id in self.prefix_cache:
            return self.prefix_cache[guild_id]
        # Fetch from db
        guild, _ = await GuildModel.get_or_create(id=guild_id)
        self.prefix_cache[guild_id] = guild.prefix
        return guild.prefix

    async def on_ready(self):
        print("Ready!")
