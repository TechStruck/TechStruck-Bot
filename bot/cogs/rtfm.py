import warnings

import aiohttp
from discord import Color, Embed
from discord.ext import commands, flags

from bot.bot import TechStruckBot
from bot.utils import fuzzy, rtfm


class RTFM(commands.Cog):
    """Search through manuals of several python modules and python itself"""

    targets = {
        "python": "https://docs.python.org/3",
        "discord.py": "https://discordpy.readthedocs.io/en/latest",
        "numpy": "https://numpy.readthedocs.io/en/latest",
        "pandas": "https://pandas.pydata.org/docs",
        "pillow": "https://pillow.readthedocs.io/en/stable",
        "imageio": "https://imageio.readthedocs.io/en/stable",
        "requests": "https://requests.readthedocs.io/en/master",
        "aiohttp": "https://docs.aiohttp.org/en/stable",
        "django": "https://django.readthedocs.io/en/stable",
        "flask": "https://flask.palletsprojects.com/en/1.1.x",
        "praw": "https://praw.readthedocs.io/en/latest",
        "apraw": "https://apraw.readthedocs.io/en/latest",
        "asyncpg": "https://magicstack.github.io/asyncpg/current",
        "aiosqlite": "https://aiosqlite.omnilib.dev/en/latest",
        "sqlalchemy": "https://docs.sqlalchemy.org/en/14",
        "tensorflow": "https://www.tensorflow.org/api_docs/python",
        "matplotlib": "https://matplotlib.org/stable",
        "seaborn": "https://seaborn.pydata.org",
        "pygame": "https://www.pygame.org/docs",
        "simplejson": "https://simplejson.readthedocs.io/en/latest",
        "wikipedia": "https://wikipedia.readthedocs.io/en/latest",
    }

    aliases = {
        ("py", "py3", "python3", "python"): "python",
        ("dpy", "discord.py", "discordpy"): "discord.py",
        ("np", "numpy", "num"): "numpy",
        ("pd", "pandas", "panda"): "pandas",
        ("pillow", "pil"): "pillow",
        ("imageio", "imgio", "img"): "imageio",
        ("requests", "req"): "requests",
        ("aiohttp", "http"): "aiohttp",
        ("django", "dj"): "django",
        ("flask", "fl"): "flask",
        ("reddit", "praw", "pr"): "praw",
        ("asyncpraw", "apraw", "apr"): "apraw",
        ("asyncpg", "pg"): "asyncpg",
        ("aiosqlite", "sqlite", "sqlite3", "sqli"): "aiosqlite",
        ("sqlalchemy", "sql", "alchemy", "alchem"): "sqlalchemy",
        ("tensorflow", "tf"): "tensorflow",
        ("matplotlib", "mpl", "plt"): "matplotlib",
        ("seaborn", "sea"): "seaborn",
        ("pygame", "pyg", "game"): "pygame",
        ("simplejson", "sjson", "json"): "simplejson",
        ("wiki", "wikipedia"): "wikipedia",
    }

    url_overrides = {
        "tensorflow": "https://github.com/mr-ubik/tensorflow-intersphinx/raw/master/tf2_py_objects.inv"
    }

    def __init__(self, bot: TechStruckBot) -> None:
        self.bot = bot
        self.cache = {}

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.http._HTTPClient__session  # type: ignore

    async def build(self, target) -> None:
        url = self.targets[target]
        req = await self.session.get(
            self.url_overrides.get(target, f'{url}/objects.inv')
        )

        if req.status != 200:
            warnings.warn(
                Warning(
                    f"Received response with status code {req.status} when trying to build RTFM cache for {target} through {url}/objects.inv"
                )
            )
            raise commands.CommandError("Failed to build RTFM cache")
        self.cache[target] = rtfm.SphinxObjectFileReader(
            await req.read()
        ).parse_object_inv(url)

    @commands.group(invoke_without_command=True)
    async def rtfm(self, ctx: commands.Context, doc: str, *, term: str = None):
        """
        Search through docs of a module/python
        Args: target, term
        """
        doc = doc.lower()
        target = None
        for aliases, target_name in self.aliases.items():
            if doc in aliases:
                target = target_name

        if not target:
            return await ctx.reply("Alias/target not found")
        if not term:
            return await ctx.reply(self.targets[target])

        cache = self.cache.get(target)
        if not cache:
            await ctx.trigger_typing()
            await self.build(target)
            cache = self.cache.get(target)

        results = fuzzy.finder(term, list(cache.items()), key=lambda x: x[0], lazy=False)[:8]  # type: ignore

        if not results:
            return await ctx.reply("Couldn't find any results")

        await ctx.reply(
            embed=Embed(
                title=f"Searched in {target}",
                description="\n".join([f"[`{key}`]({url})" for key, url in results]),
                color=Color.dark_purple(),
            )
        )

    @rtfm.command(name="list")
    async def list_targets(self, ctx: commands.Context):
        """List all the avaliable documentation search targets"""
        aliases = {v: k for k, v in self.aliases.items()}
        embed = Embed(title="RTFM list of avaliable modules", color=Color.green())
        embed.description = "\n".join(
            [
                "[{0}]({1}): {2}".format(
                    target,
                    link,
                    "\u2800".join([f"`{i}`" for i in aliases[target] if i != target]),
                )
                for target, link in self.targets.items()
            ]
        )

        await ctx.send(embed=embed)

    @flags.add_flag("aliases", nargs="+")
    @flags.add_flag("url")
    @flags.add_flag("name")
    @flags.add_flag("--override", "-o")
    @rtfm.command(name="add", hidden=True, cls=flags.FlagCommand)
    @commands.is_owner()
    async def add_target(self, ctx: commands.Context, **kwargs):
        print(kwargs)
        name, url, aliases, override = (
            kwargs.pop("name"),
            kwargs.pop("url"),
            kwargs.pop("aliases"),
            kwargs.pop("override"),
        )
        print(name, url, aliases, override)
        self.targets[name] = url
        self.aliases[tuple(aliases)] = name
        if override:
            self.url_overrides[name] = override

        await ctx.send(
            "RTFM target {name} added with aliases {aliases}".format(
                name=name, aliases=aliases
            )
        )


def setup(bot: TechStruckBot):
    bot.add_cog(RTFM(bot))
