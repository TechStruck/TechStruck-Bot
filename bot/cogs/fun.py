from discord.ext import commands
from discord import Member, Embed, Color


class Fun(commands.Cog):
    """Commands for fun and entertainment"""

    def __init__(self, bot: commands.Cog):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
