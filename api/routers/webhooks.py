import datetime
import json
import random
from concurrent import futures
from typing import Iterable, List

from aiohttp import ClientSession
from discord import AsyncWebhookAdapter, Color, Embed, RequestsWebhookAdapter, Webhook
from fastapi import APIRouter, Depends
from praw import Reddit

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

def send_meme(webhook: Webhook, subreddits:List[str]) -> bool:
    meme_subreddit = reddit.subreddit(random.choice(subreddits))
    meme = meme_subreddit.random()
    if not any((meme.url.endswith(i) for i in REDDIT_ALLOWED_FORMATS)):
        return False
    embed = Embed(title=meme.title, color=Color.magenta())
    embed.set_image(url=meme.url)
    embed.set_footer(text=f"\U0001f44d {meme.ups} \u2502 \U0001f44e {meme.downs}")
    webhook.send(embed=embed)
    return True

# The subreddits arg exists although theres a
# global so that in the future it can be
# modified for multiple channels/servers
def send_memes(webhook: Webhook, subreddits: Iterable[str], quantity: int):
    sent = 0
    skipped = 0
    with futures.ThreadPoolExecutor() as tp:
        while sent < quantity:
            results = [tp.submit(send_meme, webhook, subreddits) for _ in range(quantity-sent)]
            new_sent = sum([r.result() for r in results])
            skipped += (quantity-sent) - new_sent
            sent += new_sent
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

    tip_no = (datetime.date.today() - datetime.date(2021, 1, 31)).days

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
