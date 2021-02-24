import re

from discord import Color, Embed
from discord.ext import commands

from config.bot import bot_config


# TODO: Move this into utils
async def create_guest_paste_bin(session, code):
    res = await session.post(
        "https://pastebin.com/api/api_post.php",
        data={
            "api_dev_key": bot_config.pastebin_api_key,
            "api_paste_code": code,
            "api_paste_private":0,
            "api_paste_name": "output.txt",
            "api_paste_expire_date": "1D",
            "api_option":"paste",
        })
    return await res.text()

 

class CodeExec(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # TODO: Improve this further
        self.regex = re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")

    @property
    def session(self):
        return self.bot.http._HTTPClient__session

    async def _run_code(self, *, lang: str, code: str):
        res = await self.session.post(
            "https://emkc.org/api/v1/piston/execute",
            json={"language": lang, "source": code})
        return await res.json()

    @commands.command()
    async def run(self, ctx: commands.Context, *, codeblock: str):
        """
        Run code and get results instantly
        **Note**: You must use codeblocks around the code
        """
        matches = self.regex.findall(codeblock)
        if not matches:
            return await ctx.reply(embed=Embed(title="Uh-oh", description="Couldn't quite see your codeblock"))
        lang = matches[0][0] or matches[0][1]
        if not lang:
            return await ctx.reply(embed=Embed(title="Uh-oh", description="Couldn't find the language hinted in the codeblock or before it"))
        code = matches[0][2]
        result = await self._run_code(lang=lang, code=code)

        await self._send_result(ctx, result)

    @commands.command()
    async def runl(self, ctx:commands.Context, lang:str, *, code:str):
        """
        Run a single line of code, **must** specify language as first argument
        """
        result = await self._run_code(lang=lang, code=code)
        await self._send_result(ctx, result)



    async def _send_result(self, ctx:commands.Context, result:dict):
        if "message" in result:
            return await ctx.reply(embed=Embed(title="Uh-oh", description=result["message"], color=Color.red()))
        output = result['output']
#        if len(output) > 2000:
#            url = await create_guest_paste_bin(self.session, output)
#            return await ctx.reply("Your output was too long, so here's the pastebin link " + url)
        embed = Embed(
            title=f"Ran your {result['language']} code", color=Color.green())
        output = output[:500]
        shortened = (len(output)>500)
        lines = output.splitlines()
        shortened = shortened or (len(lines)>15)
        output = "\n".join(lines[:15])
        output += shortened * "\n\n**Output shortened**"
        embed.add_field(name="Output", value=output or "**<No output>**")

        await ctx.reply(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(CodeExec(bot))
