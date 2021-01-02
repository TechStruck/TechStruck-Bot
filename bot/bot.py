from discord.ext import commands


class TechStruckBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.')

    async def on_ready(self):
        print("Ready!")
