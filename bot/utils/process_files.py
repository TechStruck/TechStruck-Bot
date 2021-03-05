import re
from typing import Dict, List, Tuple

from discord.ext import commands

files_pattern = re.compile(r"\s{0,}```\w{0,}\s{0,}")


class NoValidFiles(commands.CommandError):
    def __str__(self):
        return "None of the files were valid or no files were given"


async def process_files(
    ctx: commands.Context, inp: str
) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    files = {}

    attachments = ctx.message.attachments.copy()
    skipped = []
    msg = ctx.message

    # If the message was a reply
    if msg.reference and msg.reference.message_id:
        replied = msg.reference.cached_message or await msg.channel.fetch_message(
            msg.reference.message_id
        )
        attachments.extend(replied.attachments)

    if inp:
        # TODO: Change this to something better
        files_and_names = files_pattern.split(inp)[:-1]

        # Dict comprehension to create the files 'object'
        files = {
            name: {"content": content + "\n"}
            for name, content in zip(files_and_names[0::2], files_and_names[1::2])
        }

    for attachment in attachments:
        if attachment.size > 16 * 1024 or attachment.filename.endswith(
            ("jpg", "jpeg", "png")
        ):
            skipped.append(attachment.filename)
            continue
        try:
            b = (await attachment.read()).decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(attachment.filename)
        else:
            files[attachment.filename] = {"content": b}

    if not files:
        raise NoValidFiles()

    return files, skipped
