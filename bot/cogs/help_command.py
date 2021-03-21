import discord
from discord.ext import commands

bot_links = """[Support](https://discord.gg/KgZRMch3b6)\u2800\
[Github](https://github.com/FalseDev/Tech-struck)\u2800\
[Suggestions](https://github.com/FalseDev/Tech-struck/issues)"""


class HelpCommand(commands.HelpCommand):
    """
    An Embed help command
    Based on https://gist.github.com/Rapptz/31a346ed1eb545ddeb0d451d81a60b3b
    """

    COLOUR = discord.Colour.greyple()

    def get_ending_note(self):
        return "Use {0}{1} [command] for more info on a command.".format(
            self.clean_prefix, self.invoked_with
        )

    def get_command_signature(self, command):
        return "{0.qualified_name} {0.signature}".format(command)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Bot Commands", colour=self.COLOUR)
        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, cmds in mapping.items():
            if cog is None:
                continue
            name = cog.qualified_name
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                value = "\u2002".join(f"`{c.name}`" for c in cmds)
                if cog and cog.description:
                    value = "{0}\n{1}".format(cog.description, value)

                embed.add_field(name=name, value=value)

        embed.set_footer(text=self.get_ending_note())
        self.add_support_server(embed)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title="{0.qualified_name} Commands".format(cog), colour=self.COLOUR
        )
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(
                name=command.qualified_name,
                value=command.short_doc or "...",
                inline=False,
            )

        embed.set_footer(text=self.get_ending_note())
        self.add_support_server(embed)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOUR)
        if group.help:
            embed.description = group.help

        filtered = await self.filter_commands(group.commands, sort=True)
        for command in filtered:
            embed.add_field(
                name=command.qualified_name,
                value=command.short_doc or "...",
                inline=False,
            )

        embed.set_footer(text=self.get_ending_note())
        self.add_support_server(embed)
        await self.get_destination().send(embed=embed)

    def add_support_server(self, embed):
        return embed.add_field(name="Links", value=bot_links, inline=False)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.qualified_name, colour=self.COLOUR)
        embed.add_field(name="Signatute", value=self.get_command_signature(command))
        if command.help:
            embed.description = command.help

        embed.set_footer(text=self.get_ending_note())
        self.add_support_server(embed)
        await self.get_destination().send(embed=embed)


def setup(bot: commands.Bot):
    bot._default_help_command = bot.help_command
    bot.help_command = HelpCommand()


def teardown(bot):
    bot.help_command = bot._default_help_command
