import asyncio
import re
import traceback
from typing import Iterable

from discord import Color, Embed, Intents, Message
from discord.ext import commands, tasks
from discord.mentions import AllowedMentions
from tortoise import Tortoise

from models import GuildModel


class TechStruckBot(commands.Bot):
    def __init__(self, *, tortoise_config, load_extensions=True, loadjsk=True):
        allowed_mentions = AllowedMentions(
            users=True, replied_user=True, roles=False, everyone=False
        )
        super().__init__(
            command_prefix=self.get_custom_prefix,
            intents=Intents.all(),
            allowed_mentions=allowed_mentions,
            description="A bot by and for developers to integrate several tools into one place.",
        )
        self.tortoise_config = tortoise_config
        self.db_connected = False
        self.prefix_cache = {}
        self.loop.create_task(self.create_db())

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
                )
            )
        if loadjsk:
            self.load_extension("jishaku")

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
        await self.process_commands(msg)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            await super().on_command_error(ctx, error)
            await ctx.send("Oopsy, something's broken")
        title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
        await ctx.send(
            embed=Embed(title=title, description=str(error), color=Color.red())
        )

    async def get_custom_prefix(self, _, message: Message):
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
