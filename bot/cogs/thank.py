import asyncio
from typing import Optional

from discord import Color, Embed, Member, Reaction
from discord.ext import commands
from tortoise.functions import Count, Q

from models import ThankModel, UserModel

delete_thank_message = """**Thanked**: <@!{0.thanked_id}>
**Thanker**: <@!{0.thanker_id}>
**Description**: {0.description}
**Time**: {0.time}\n
Confirmation required!"""

thank_list_message = """`{0.time:%D %T}` ID:`{0.id}`
From: <@!{0.thanker_id}> ({0.thanker_id})
Description: {0.description}\n"""


class Thank(commands.Cog):
    """Commands related to thanking members/helpers for help received"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.cooldown(5, 300, commands.BucketType.user)
    async def thank(self, ctx: commands.Context, recv: Member, *, description: str):
        """Thank someone for their help with a description to show gratitude"""
        if recv.id == ctx.author.id:
            return await ctx.send(
                embed=Embed(
                    title="Bruh",
                    description="You can't thank yourselves",
                    color=Color.red(),
                )
            )
        if recv.bot:
            return await ctx.send(
                embed=Embed(
                    title="Bruh", description="You can't thank a bot", color=Color.red()
                )
            )
        # TODO: Convert this to an expression (?) for efficiency
        thanked, _ = await UserModel.get_or_create(id=recv.id)
        thanker, _ = await UserModel.get_or_create(id=ctx.author.id)
        await ThankModel.create(
            thanker=thanker,
            thanked=thanked,
            description=description,
            guild_id=ctx.guild.id,
        )
        await ctx.send(f"You have thanked {recv}")

    @thank.command(name="stats", aliases=["check"])
    async def thank_stats(
        self, ctx: commands.Context, *, member: Optional[Member] = None
    ):
        """View stats for thanks you've received and sent, in the current server and globally"""
        member = member or ctx.author
        sent_thanks = await ThankModel.filter(thanker__id=member.id).count()
        recv_thanks = await ThankModel.filter(thanked__id=member.id).count()
        server_sent_thanks = await ThankModel.filter(
            thanker__id=member.id, guild__id=ctx.guild.id
        ).count()
        server_recv_thanks = await ThankModel.filter(
            thanked__id=member.id, guild__id=ctx.guild.id
        ).count()

        embed = Embed(title=f"Thank stats for: {member}", color=Color.green())
        embed.add_field(
            name="Thanks received",
            value="Global: {}\nThis server: {}".format(recv_thanks, server_recv_thanks),
        )
        embed.add_field(
            name="Thanks sent",
            value="Global: {}\nThis server: {}".format(sent_thanks, server_sent_thanks),
        )
        await ctx.send(embed=embed)

    @thank.command(name="leaderboard", aliases=["lb"])
    async def thank_leaderboard(self, ctx: commands.Context):
        """View a leaderboard of top helpers in the current server"""
        await ctx.trigger_typing()
        lb = (
            await UserModel.annotate(
                thank_count=Count("thanks", _filter=Q(thanks__guild_id=ctx.guild.id))
            )
            .filter(thank_count__gt=0)
            .order_by("-thank_count")
            .limit(5)
        )
        if not lb:
            return await ctx.send(
                embed=Embed(
                    title="Oopsy",
                    description="There are no thanks here yet!",
                    color=Color.red(),
                )
            )
        invis = "\u2800"
        embed = Embed(
            title="LeaderBoard",
            color=Color.blue(),
            description="\n\n".join(
                [
                    f"**{m.thank_count} Thanks**{invis * (4 - len(str(m.thank_count)))}<@!{m.id}>"
                    for m in lb
                ]
            ),
        )
        await ctx.send(embed=embed)

    @thank.command(name="delete")
    @commands.has_guild_permissions(kick_members=True)
    async def delete_thank(self, ctx: commands.Context, thank_id: int):
        """Remove an invalid/fake thank record"""
        thank = await ThankModel.get_or_none(pk=thank_id, guild_id=ctx.guild.id)
        if not thank:
            return await ctx.send("Thank with given ID not found")
        msg = await ctx.send(
            embed=Embed(
                title="Delete thank",
                description=delete_thank_message.format(thank),
            )
        )
        await msg.add_reaction("\u2705")
        await msg.add_reaction("\u274e")

        def check(r: Reaction, u: Member):
            return u.id == ctx.author.id and str(r.emoji) in ("\u2705", "\u274e")

        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check)
        except asyncio.TimeoutError:
            return await ctx.reply("Cancelled.")
        if str(r.emoji) == "\u2705":
            await thank.delete()
            return await ctx.reply("Deleted.")
        return await ctx.reply("Cancelled.")

    @thank.command(name="list")
    @commands.has_guild_permissions(kick_members=True)
    async def list_thanks(self, ctx: commands.Context, member: Member):
        """List the most recent 10 thanks received by a user in the current server"""
        thanks = (
            await ThankModel.filter(thanked_id=member.id, guild_id=ctx.guild.id)
            .order_by("-time")
            .limit(10)
        )

        await ctx.send(
            embed=Embed(
                title="Listing",
                description="\n".join([thank_list_message.format(t) for t in thanks]),
                color=Color.dark_blue(),
            )
        )


def setup(bot: commands.Bot):
    bot.add_cog(Thank(bot))
