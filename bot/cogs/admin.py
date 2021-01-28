from discord.ext import commands
from discord.utils import get
from utils.embed import yaml_file_to_message


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _refresh(self, ctx: commands.Context, filename: str, channel_name: str):
        target_channel = get(ctx.guild.text_channels,
                             name=channel_name)
        async for msg in target_channel.history():
            if msg.author.id == self.bot.user.id:
                target = msg
        m, e, _ = yaml_file_to_message(filename)
        await target.edit(message=m, embed=e)

    @commands.group(name="refresh", invoke_without_subcommand=False)
    @commands.is_owner()
    async def refresh(self, ctx: commands.Context):
        pass

    @refresh.command(name="roles")
    async def refresh_roles(self, ctx: commands.Context):
        await self._refresh(ctx, "./yaml_embeds/roles.yaml", "\U0001f3c5\u2502roles")

    @refresh.command(name="rules")
    async def refresh_rules(self, ctx: commands.Context):
        await self._refresh(ctx, "./yaml_embeds/rules.yaml", "\u2502rules")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
