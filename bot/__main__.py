import os
from discord.ext import commands
from .bot import TechStruckBot

os.environ.setdefault('JISHAKU_HIDE', '1')
os.environ.setdefault('JISHAKU_RETAIN', '1')
os.environ.setdefault('JISHAKU_NO_UNDERSCORE', '1')

if __name__ == '__main__':
    import config
    bot = TechStruckBot()
    bot.run(config.BOT_TOKEN)
