import asyncio

from discord import Color, Embed, Forbidden, Member, utils
from discord.ext import commands

from bot.bot import TechStruckBot


class Fun(commands.Cog):
    """Commands for fun and entertainment"""

    def __init__(self, bot: TechStruckBot):
        self.bot = bot

    @commands.command()
    async def beer(
        self, ctx, user: Member = None, *, reason: commands.clean_content = None
    ):
        """Have virtual beer with your friends/fellow members"""
        if not user or user.id == ctx.author.id:
            return await ctx.send(f"{ctx.author.name}: paaaarty!:tada::beer:")
        if user.id == self.bot.user.id:
            return await ctx.send("drinks beer with you* :beers:")
        if user.bot:
            return await ctx.send(f"lol {ctx.author.name}lol")

        beer_offer = f"{user.name}, you got a :beer: offer from {ctx.author.name}"
        beer_offer = beer_offer + f"\n\nReason: {reason}" if reason else beer_offer
        msg = await ctx.send(beer_offer)

        def reaction_check(reaction, m):
            return m.id == user.id and str(reaction.emoji) == "🍻"

        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for("reaction_add", timeout=30.0, check=reaction_check)
            await msg.edit(
                content=f"{user.name} and {ctx.author.name} are enjoying a lovely beer together :beers:"
            )
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send(
                f"well, doesn't seem like {user.name} wanted a beer with you {ctx.author.name} ;-;"
            )
        except Forbidden:
            beer_offer = f"{user.name}, you got a :beer: from {ctx.author.name}"
            beer_offer = beer_offer + f"\n\nReason: {reason}" if reason else beer_offer
            await msg.edit(content=beer_offer)

    @commands.command()
    async def beers(
        self,
        ctx: commands.Context,
        members: commands.Greedy[Member],
        *,
        reason: commands.clean_content = None,
    ):
        """Invite a bunch of people to have beer"""
        if not members:
            return await ctx.send("You can't have beer with no other person!")
        for member in members:
            if member.bot:
                return await ctx.send("Beer with bots isn't exactly a thing...")

        message = (
            ", ".join(m.display_name for m in members)
            + "\nYou have been invited for beer \U0001f37b by "
            + ctx.author.display_name
            + ((" Reason: " + reason) if reason else "")
        )

        msg = await ctx.send(message)
        await msg.add_reaction("\U0001f37b")

        def check(r, m):
            return m in members and r.message == msg and str(r.emoji) == "\U0001f37b"

        while True:
            try:
                r, _ = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await msg.edit(
                    content="Ouch, looks like not everyone wants beer now..."
                )
            else:
                if set(
                    m.id for m in await r.message.reactions[0].users().flatten()
                ).issuperset(m.id for m in members):
                    content = (
                        ", ".join(
                            utils.escape_mentions(m.display_name) for m in members
                        )
                        + ", "
                        + utils.escape_mentions(ctx.author.display_name)
                        + " enjoy a lovely beer together \U0001f37b"
                    )

                    return await msg.edit(content=content)

    @commands.command()
    async def beerparty(
        self, ctx: commands.Context, *, reason: commands.clean_content = None
    ):
        """Openly allow anyone to join and enjoy in a beer party"""
        reason = ("\nReason:" + reason) if reason else ""
        msg = await ctx.send(f"Open invite to a beer party!{reason}")
        await msg.add_reaction("\U0001f37b")
        await asyncio.sleep(20)
        users = (
            await (await ctx.channel.fetch_message(msg.id))
            .reactions[0]
            .users()
            .flatten()
        )
        await ctx.send(
            ", ".join(
                [
                    utils.escape_mentions(u.display_name)
                    for u in users + ([] if ctx.author in users else [ctx.author])
                    if not u.bot
                ]
            )
            + " enjoy a lovely beer paaarty \U0001f37b"
        )


def setup(bot: TechStruckBot):
    bot.add_cog(Fun(bot))
