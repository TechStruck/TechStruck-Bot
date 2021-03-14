from discord.channel import TextChannel
from discord.ext import commands, flags

from bot.utils.embed_flag_input import embed_input, dict_to_embed

from bot.bot import TechStruckBot


class Utils(commands.Cog):
    """Utility commands"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @embed_input
    @flags.add_flag("--channel", "--in", type=TextChannel, default=None)
    @flags.add_flag("--message", "--msg", "-m", default=None)
    @flags.command()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.bot_has_guild_permissions()
    async def embed(self, ctx: commands.Context, **kwargs):
        """Send an embed with any fields, in any channel, with a command line like arguments"""
        embed = dict_to_embed(kwargs)
        target = kwargs.pop("channel") or ctx
        message = kwargs.pop("message")
        # TODO: Replace `ping:roleid` or `ping:"rolename"` by the actual ping
        await target.send(message, embed=embed)
        await ctx.message.add_reaction("\u2705")


def setup(bot: TechStruckBot):
    bot.add_cog(Utils(bot))
