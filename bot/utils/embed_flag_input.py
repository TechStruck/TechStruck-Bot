import re
from typing import Dict, TypeVar, Union
from urllib import parse

from discord import AllowedMentions, Embed, Member, User
from discord.ext import commands, flags

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


_embed_field_flags = (
    [
        flags.add_flag(*flagname)
        for flagname in (
            # Basic
            ("--title", "-t"),
            ("--description", "-d"),
            # Author
            ("--authorname", "--aname", "-an"),
            # Footer
            ("--footertext", "-ft"),
        )
    ]
    + [
        flags.add_flag(*flagname, type=url_type)
        for flagname in (
            # Image parts
            ("--thumbnail", "-th"),
            ("--authorurl", "--aurl", "-au"),
            ("--authoricon", "--aicon", "-ai"),
            ("--footericon", "-fi"),
            ("--image", "-i"),
        )
    ]
    + [
        flags.add_flag("--fields", "-f", nargs="+"),
        flags.add_flag("--colour", "--color", "-c", type=colortype),
        flags.add_flag("--autoauthor", "-aa", action="store_true", default=False),
    ]
)

_allowed_mentions_flags = (
    flags.add_flag("--everyonemention", "-em", default=False, action="store_true"),
    flags.add_flag("--rolementions", "-rm", default=False, action="store_true"),
    flags.add_flag("--usermentions", "-um", default=True, action="store_false"),
)


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


def embed_input(func: _F) -> _F:
    for flag in _embed_field_flags:
        flag(func)
    return func


def allowed_mentions_input(func: _F) -> _F:
    for flag in _allowed_mentions_flags:
        flag(func)
    return func


def dict_to_embed(data: Dict[str, str], author: Union[User, Member] = None):
    embed = Embed()
    for field in ("title", "description", "colour"):
        if (value := data.pop(field, None)) :
            setattr(embed, field, value)
    for field in "thumbnail", "image":
        if (value := data.pop(field, None)) :
            getattr(embed, "set_" + field)(url=value)

    if data.pop("autoauthor") and author:
        embed.set_author(name=author.display_name, icon_url=str(author.avatar_url))
    if "authorname" in data and data["authorname"]:
        kwargs = {}
        if (icon_url := data.pop("authoricon", None)) :
            kwargs["icon_url"] = icon_url
        if (author_url := data.pop("authorurl", None)) :
            kwargs["url"] = author_url

        embed.set_author(name=data.pop("authorname"), **kwargs)

    if "footertext" in data and data["footertext"]:
        kwargs = {}
        if (footer_icon := data.pop("footericon", None)) :
            kwargs["icon_url"] = footer_icon

        embed.set_footer(text=data.pop("footertext"), **kwargs)

    fields = data.pop("fields") or []
    if len(fields) % 2 == 1:
        raise InvalidFieldArgs(
            "Number of arguments for fields must be an even number, pairs of name and value"
        )

    for name, value in zip(fields[::2], fields[1::2]):
        embed.add_field(name=name, value=value)

    if embed.to_dict() == {"type": "rich"}:
        raise EmbeyEmbedError()

    return embed


def dict_to_allowed_mentions(data):
    return AllowedMentions(
        everyone=data.pop("everyonemention"),
        roles=data.pop("rolementions"),
        users=data.pop("usermentions"),
    )
