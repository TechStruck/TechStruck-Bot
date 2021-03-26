import functools
import re
from typing import Dict, Iterable, TypeVar, Union
from urllib import parse

from discord import AllowedMentions, Embed, Member, User
from discord.ext import commands, flags  # type: ignore

_F = TypeVar(
    "_F",
)


class InvalidFieldArgs(commands.CommandError):
    pass


class EmbeyEmbedError(commands.CommandError):
    def __str__(self) -> str:
        return "The embed has no fields/attributes populated"


class InvalidUrl(commands.CommandError):
    def __init__(self, invalid_url: str, *, https_only: bool = False) -> None:
        self.invalid_url = invalid_url
        self.https_only = https_only

    def __str__(self) -> str:
        return "The url entered (`%s`) is invalid.%s" % (
            self.invalid_url,
            "\nThe url must be https" if self.https_only else "",
        )


class InvalidColor(commands.CommandError):
    def __init__(self, value) -> None:
        self.value = value

    def __str__(self):
        return "%s isn't a valid color, eg: `#fff000`, `f0f0f0`" % self.value


class UrlValidator:
    def __init__(self, *, https_only=False) -> None:
        self.https_only = https_only

    def __call__(self, value):
        url = parse.urlparse(value)
        schemes = ("https",) if self.https_only else ("http", "https")
        if url.scheme not in schemes or not url.hostname:
            raise InvalidUrl(value, https_only=self.https_only)
        return value


def colortype(value: str):
    try:
        return int(value.removeprefix("#"), base=16)
    except ValueError:
        raise InvalidColor(value)


url_type = UrlValidator(https_only=True)


def process_message_mentions(message: str) -> str:
    if not message:
        return ""
    for _type, _id in re.findall(r"(role|user):(\d{18})", message):
        message = message.replace(
            _type + ":" + _id, f"<@!{_id}>" if _type == "user" else f"<@&{_id}>"
        )
    for label in ("mention", "ping"):
        for role in ("everyone", "here"):
            message = message.replace(label + ":" + role, f"@{role}")
    return message


class FlagAdder:
    def __init__(self, kwarg_map: Dict[str, Iterable], *, default_mode: bool = False):
        self.kwarg_map = kwarg_map
        self.default_mode = default_mode

    def call(self, func: _F, **kwargs) -> _F:
        if kwargs.pop("all", False):
            for flags in self.kwarg_map.values():
                self.apply(flags=flags, func=func)
            return func
        kwargs = {**{k: self.default_mode for k in self.kwarg_map.keys()}, **kwargs}
        for k, v in kwargs.items():
            if v:
                self.apply(flags=self.kwarg_map[k], func=func)
        return func

    def __call__(self, func=None, **kwargs):
        if func is None:
            return functools.partial(self.call, **kwargs)
        return self.call(func, **kwargs)

    def apply(self, *, flags: Iterable, func: _F) -> _F:
        for flag in flags:
            flag(func)
        return func


embed_input = FlagAdder(
    {
        "basic": (
            flags.add_flag("--title", "-t"),
            flags.add_flag("--description", "-d"),
            flags.add_flag("--fields", "-f", nargs="+"),
            flags.add_flag("--colour", "--color", "-c", type=colortype),
        ),
        "image": (
            flags.add_flag("--thumbnail", "-th", type=url_type),
            flags.add_flag("--image", "-i", type=url_type),
        ),
        "author": (
            flags.add_flag("--author-name", "--aname", "-an"),
            flags.add_flag("--auto-author", "-aa", action="store_true", default=False),
            flags.add_flag("--author-url", "--aurl", "-au", type=url_type),
            flags.add_flag("--author-icon", "--aicon", "-ai", type=url_type),
        ),
        "footer": (
            flags.add_flag("--footer-icon", "-fi", type=url_type),
            flags.add_flag("--footer-text", "-ft"),
        ),
    }
)


allowed_mentions_input = FlagAdder(
    {
        "all": (
            flags.add_flag(
                "--everyone-mention", "-em", default=False, action="store_true"
            ),
            flags.add_flag(
                "--role-mentions", "-rm", default=False, action="store_true"
            ),
            flags.add_flag(
                "--user-mentions", "-um", default=True, action="store_false"
            ),
        )
    },
    default_mode=True,
)

webhook_input = FlagAdder(
    {
        "all": (
            flags.add_flag("--webhook", "-w", action="store_true", default=False),
            flags.add_flag("--webhook-username", "-wun", type=str, default=None),
            flags.add_flag("--webhook-avatar", "-wav", type=url_type, default=None),
            flags.add_flag(
                "--webhook-auto-author", "-waa", action="store_true", default=False
            ),
            flags.add_flag("--webhook-new-name", "-wnn", type=str, default=None),
            flags.add_flag("--webhook-name", "-wn", type=str, default=None),
            flags.add_flag(
                "--webhook-dispose", "-wd", action="store_true", default=False
            ),
        )
    },
    default_mode=True,
)


def dict_to_embed(data: Dict[str, str], author: Union[User, Member] = None):
    embed = Embed()
    for field in ("title", "description", "colour"):
        if (value := data.pop(field, None)) :
            setattr(embed, field, value)
    for field in "thumbnail", "image":
        if (value := data.pop(field, None)) :
            getattr(embed, "set_" + field)(url=value)

    if data.pop("auto_author", False) and author:
        embed.set_author(name=author.display_name, icon_url=str(author.avatar_url))
    if "author_name" in data and data["author_name"]:
        kwargs = {}
        if (icon_url := data.pop("author_icon", None)) :
            kwargs["icon_url"] = icon_url
        if (author_url := data.pop("author_url", None)) :
            kwargs["url"] = author_url

        embed.set_author(name=data.pop("author_name"), **kwargs)

    if "footer_text" in data and data["footer_text"]:
        kwargs = {}
        if (footer_icon := data.pop("footer_icon", None)) :
            kwargs["icon_url"] = footer_icon

        embed.set_footer(text=data.pop("footer_text"), **kwargs)

    fields = data.pop("fields", []) or []
    if len(fields) % 2 == 1:
        raise InvalidFieldArgs(
            "Number of arguments for fields must be an even number, pairs of name and value"
        )

    for name, value in zip(fields[::2], fields[1::2]):
        embed.add_field(name=name, value=value, inline=False)

    if embed.to_dict() == {"type": "rich"}:
        raise EmbeyEmbedError()

    return embed


def dict_to_allowed_mentions(data):
    return AllowedMentions(
        everyone=data.pop("everyone_mention"),
        roles=data.pop("role_mentions"),
        users=data.pop("user_mentions"),
    )
