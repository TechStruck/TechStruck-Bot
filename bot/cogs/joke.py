import asyncio
import re

from discord.ext import commands
from discord import Embed, Color, Message, TextChannel, RawReactionActionEvent, utils

from models import JokeModel, UserModel

joke_format = """**Setup**: {0.setup}\n
**End**: {0.end}\n
**Server**: {1.name} (`{1.id}`)\n
**Username**: {2} (`{2.id}`)\n
Joke ID: {0.id}"""

class Joke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def joke(self, ctx: commands.Context):
        await ctx.send_help(self.joke)

    @joke.command()
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def add(self, ctx: commands.Context):
        try:
            setup = await self._get_input(
                ctx,
                "Enter joke setup",
                "Enter the question/setup to be done before answering/finishing the joke",
            )
            end = await self._get_input(
                ctx, "Enter joke end", "Enter the text to be used to finish the joke"
            )
        except asyncio.TimeoutError:
            return await ctx.send("You didn't answer")

        await UserModel.get_or_create(id=ctx.author.id)
        joke = await JokeModel.create(setup=setup, end=end, creator_id=ctx.author.id)

        msg = await self.joke_entries_channel.send(
            embed=Embed(
                title=f"Joke #{joke.id}",
                description=joke_format.format(
                    joke, ctx.guild, ctx.author
                ),
                color=Color.dark_gold(),
            )
        )
        await ctx.send("Your submission has been recorded!")

        await msg.add_reaction("\u2705")
        await msg.add_reaction("\u274e")
        await self.joke_entries_channel.send("<@&815237052639477792>", delete_after=1)

    @property
    def joke_entries_channel(self) -> TextChannel:
        return self.bot.get_channel(815237244218114058)

    async def _get_input(self, ctx: commands.Context, title: str, description: str):
        await ctx.send(
            embed=Embed(title=title, description=description, color=Color.dark_blue())
        )

        def check(m: Message):
            return m.author == ctx.author and m.channel == ctx.channel

        res: Message = await self.bot.wait_for("message", check=check, timeout=120)
        return await commands.clean_content().convert(ctx, res.content)

    @commands.Cog.listener("on_raw_reaction_add")
    @commands.Cog.listener("on_raw_reaction_remove")
    async def reaction_listener(self, payload: RawReactionActionEvent):
        if payload.channel_id != 815237244218114058:
            return
        msg: Message = await self.joke_entries_channel.fetch_message(payload.message_id)

        up_reaction = utils.get(msg.reactions, emoji="\u2705")
        down_reaction = utils.get(msg.reactions, emoji="\u274e")
        ups = (up_reaction and await up_reaction.users().flatten()) or []
        # downs = (down_reaction and await up_reaction.users().flatten()) or []
        # TODO: Add further stuff here for downvotes checking etc

        embed = msg.embeds[0]
        if len(ups) > 3:
            await JokeModel.filter(id=int(embed.title[6:])).update(accepted=True)
            embed.color = Color.green()
            await msg.edit(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Joke(bot))
