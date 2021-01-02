import traceback
from typing import List
from discord.ext import commands


class TechStruckBot(commands.Bot):
    def __init__(self, load_extensions=True, loadjsk=True):
        super().__init__(command_prefix='.')

        if load_extensions:
            self.load_extensions(())
        if loadjsk:
            self.load_extension('jishaku')

    def load_extensions(self, extentions: List[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_ready(self):
        print("Ready!")
