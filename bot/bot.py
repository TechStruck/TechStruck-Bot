import traceback
from typing import List
from discord import Message, Member, Intents
from discord.ext import commands, tasks
from tortoise import Tortoise
from models import UserModel


class TechStruckBot(commands.Bot):
    def __init__(self, *, tortoise_config, load_extensions=True, loadjsk=True):
        super().__init__(command_prefix='.', intents=Intents.all())
        self.tortoise_config = tortoise_config
        self.connect_db.start()

        if load_extensions:
            self.load_extensions(
                ('bot.cogs.admin', 'bot.cogs.thank'))
        if loadjsk:
            self.load_extension('jishaku')

    @tasks.loop(count=1)
    async def connect_db(self):
        await Tortoise.init(self.tortoise_config)
        print("Database connected")

    def load_extensions(self, extentions: List[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_message(self, msg: Message):
        if msg.author.bot or not msg.guild or msg.guild.id not in (782517843820412948,):
            return
        await self.process_commands(msg)

    async def on_ready(self):
        print("Ready!")
