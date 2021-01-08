from typing import Optional
from discord.ext import commands
from discord import Member, Embed, Color
from bot.models import ThankModel, MemberModel


class Thank(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def thank(self, ctx: commands.Context, recv: Member, *, description: str):
        if recv.id == ctx.author.id:
            return await ctx.send(embed=Embed(title="Bruh", description="You can't thank yourselves", color=Color.red()))
        if recv.bot:
            return await ctx.send(embed=Embed(title="Bruh", description="You can't thank a bot", color=Color.red()))
        thanked, _ = await MemberModel.get_or_create(id=recv.id)
        thanker, _ = await MemberModel.get_or_create(id=ctx.author.id)
        await ThankModel.create(thanker=thanker, thanked=thanked, description=description)
        await ctx.send(f"You have thanked {recv}")

    @commands.command(name="thankstats")
    async def thank_stats(self, ctx: commands.Context, *, member: Optional[Member] = None):
        member = member or ctx.author
        mem_obj = await MemberModel.get(id=member.id).prefetch_related('thanks', 'sent_thanks')

        embed = Embed(title=f"Thank stats for: {member}", color=Color.green())
        embed.add_field(name="Thanks received", value=len(mem_obj.thanks))
        embed.add_field(name="Thanks sent", value=len(mem_obj.sent_thanks))
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Thank(bot))
