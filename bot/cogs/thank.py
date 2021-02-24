from typing import Optional

from discord import Color, Embed, Member
from discord.ext import commands
from tortoise.functions import Count, Q

from models import ThankModel, UserModel


class Thank(commands.Cog):
    """Commands related to thanking members/helpers for help received"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def thank(self, ctx: commands.Context, recv: Member, *, description: str):
        """Thank someone for their help with a description to show gratitude"""
        if recv.id == ctx.author.id:
            return await ctx.send(embed=Embed(title="Bruh", description="You can't thank yourselves", color=Color.red()))
        if recv.bot:
            return await ctx.send(embed=Embed(title="Bruh", description="You can't thank a bot", color=Color.red()))
        # TODO: Convert this to an expression (?) for efficiency
        thanked, _ = await UserModel.get_or_create(id=recv.id)
        thanker, _ = await UserModel.get_or_create(id=ctx.author.id)
        await ThankModel.create(thanker=thanker, thanked=thanked, description=description, guild_id=ctx.guild.id)
        await ctx.send(f"You have thanked {recv}")

    @commands.command(name="thankstats", aliases=["checkthanks"])
    async def thank_stats(self, ctx: commands.Context, *, member: Optional[Member] = None):
        """View stats for thanks you've received and sent, in the current server and globally"""
        member = member or ctx.author
        sent_thanks = await ThankModel.filter(thanker__id=member.id).count()
        recv_thanks = await ThankModel.filter(thanked__id=member.id).count()
        server_sent_thanks = await ThankModel.filter(thanker__id=member.id, guild__id=ctx.guild.id).count()
        server_recv_thanks = await ThankModel.filter(thanked__id=member.id, guild__id=ctx.guild.id).count()

        embed = Embed(title=f"Thank stats for: {member}", color=Color.green())
        embed.add_field(
                name="Thanks received",
                value="Global: {}\nThis server: {}".format(recv_thanks, server_recv_thanks)
            )
        embed.add_field(
                name="Thanks sent",
                value="Global: {}\nThis server: {}".format(sent_thanks, server_sent_thanks)
                )
        await ctx.send(embed=embed)

    @commands.command(name="thankleaderboard", aliases=["thanklb", "thankslb"])
    async def thank_leaderboard(self, ctx:commands.Context):
        await ctx.trigger_typing()
        lb = await UserModel.annotate(thank_count=Count("thanks", _filter=Q(thanks__guild_id=ctx.guild.id))).filter(thank_count__gt=0).order_by("-thank_count").limit(5)
        if not lb:
            return await ctx.send(embed=Embed(title="Oopsy", description="There are no thanks here yet!", color=Color.red()))
        invis = "\u2800"
        embed = Embed(title="LeaderBoard", color=Color.blue(), description="\n\n".join([
            f"**{m.thank_count} Thanks**{invis * (4 - len(str(m.thank_count)))}<@!{m.id}>"
            for m in lb
        ]))
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Thank(bot))
