from discord import Color, Embed, Message
from discord.ext import commands
from quizapi import create_quiz_api

from config.bot import bot_config


class Quiz(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = create_quiz_api(
            bot_config.quiz_api_token, async_mode=True)

    @commands.command()
    async def startquiz(self, ctx: commands.Context):
        await ctx.send("Collecting questions!")
        questions = await self.session.get_quiz(limit=5, category="linux")
        embed = Embed(title="Big Brain Time", color=Color.darker_gray())

        def check(m: Message):
            return m.channel == ctx.channel
        scoreboard = {}
        for q in questions:
            embed.clear_fields()
            desc = (q.description + "\n" if q.description else "")
            desc += " ".join(['`' + t.name + '`' for t in q.tags]) + "\n"
            for i, a in enumerate(q.answers, 65):
                desc += chr(i) + ") " + a + "\n"
            embed.add_field(name=q.question, value=desc)
            correct_answers = []
            print(q.correct_answers)
            for i in range(q.correct_answers.count(True)):
                correct_answers.append(chr(65 + q.correct_answers.index(True)))
                q.correct_answers.remove(True)
                print(correct_answers)
            await ctx.send(embed=embed)
            unanswered = True
            while unanswered:
                try:
                    resp = await self.bot.wait_for("message", check=check, timeout=45)
                except:
                    return await ctx.send("No one answered")
                # await resp.delete()
                if resp.content.upper() in (correct_answers):
                    scoreboard[resp.author.id] = scoreboard.get(
                        resp.author.id, 0) + 1
                    unanswered = False
        scores = "\n".join(
            [f"<@!{mid}>: {score}" for mid, score in sorted(scoreboard.items(), key=lambda i:i[1])])
        await ctx.send(embed=Embed(title="Results", description=scores, color=Color.green()))


def setup(bot: commands.Bot):
    bot.add_cog(Quiz(bot))
