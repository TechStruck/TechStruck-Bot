from discord.ext import commands
from bot import TechStruckBot

if __name__ == '__main__':
    import config
    bot = TechStruckBot()
    bot.run(config.BOT_TOKEN)
