from discord.ext import commands
from discord import Member, Embed, Color


class Fun(commands.Cog):
    """Commands for fun and entertainment"""

    def __init__(self, bot: commands.Cog):
        self.bot = bot
        
    @commands.command()
    async def beer(self, ctx, user: discord.Member = None, *, reason: commands.clean_content = ""):
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
            await self.bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
            await msg.edit(content=f"{user.name} and {ctx.author.name} are enjoying a lovely beer together :beers:")
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send(f"well, doesn't seem like {user.name} wanted a beer with you {ctx.author.name} ;-;")
        except discord.Forbidden:
            beer_offer = f"{user.name}, you got a :beer: from {ctx.author.name}"
            beer_offer = beer_offer + f"\n\nReason: {reason}" if reason else beer_offer
            await msg.edit(content=beer_offer)


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
