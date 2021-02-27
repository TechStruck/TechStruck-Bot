import datetime
import json
import random
from typing import List

from aiohttp import ClientSession
from praw import Reddit
from discord import RequestsWebhookAdapter, Color, Embed, Webhook
from fastapi import APIRouter, Depends

from config.reddit import reddit_config
from config.webhook import webhook_config

from ..dependencies import aiohttp_session, auth_dep

router = APIRouter(prefix="/webhooks", dependencies=[Depends(auth_dep)])

reddit = Reddit(
    **reddit_config.dict(),
    user_agent="TechStruck",
)


REDDIT_ALLOWED_FORMATS = (".jpg", ".gif", ".png", ".jpeg")
SUBREDDITS = (
    "memes",
    "meme",
    "dankmeme",
    "me_irl",
    "dankmemes",
    "showerthoughts",
    "jokes",
    "funny",
)


def send_memes(webhook: Webhook, subreddits: List[str], quantity: int):
    sent = 0
    skipped = 0
    while sent < quantity:
        meme_subreddit = reddit.subreddit(random.choice(SUBREDDITS))
        meme = meme_subreddit.random()
        if not any((meme.url.endswith(i) for i in REDDIT_ALLOWED_FORMATS)):
            skipped += 1
            continue
        embed = Embed(title=meme.title, color=Color.magenta())
        embed.set_image(url=meme.url)
        embed.set_footer(text=f"\U0001f44d {meme.ups} \u2502 \U0001f44e {meme.downs}")
        webhook.send(embed=embed)
        sent += 1
    return sent, skipped


@router.get("/meme")
def send_memes_route():
    sent, skipped = send_memes(
        Webhook.from_url(webhook_config.meme, adapter=RequestsWebhookAdapter()),
        SUBREDDITS,
        5,
    )
    return {"sent": sent, "skipped": skipped}


@router.get("/git-tip")
async def git_tip(session: ClientSession = Depends(aiohttp_session)):
    tips_json_url = "https://raw.githubusercontent.com/git-tips/tips/master/tips.json"

    async with session.get(tips_json_url) as res:
        tips = json.loads(await res.text())

    tip_no = (datetime.date.today() - datetime.date(2021, 1, 28)).days

    tip = tips[tip_no]

    await Webhook.from_url(
        webhook_config.git_tips, adapter=AsyncWebhookAdapter(session)
    ).send(
        "<@&804403893760688179>",
        embed=Embed(
            title=tip["title"],
            description="```sh\n" + tip["tip"] + "```",
            color=Color.green(),
        ).set_footer(text="Tip {}".format(tip_no)),
        avatar_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Git_icon.svg/2000px-Git_icon.svg.png",
    )
    return {"status": "success"}
