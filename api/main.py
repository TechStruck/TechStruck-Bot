import datetime
import random
from typing import List
import json

from discord import Embed, Color, Webhook, AsyncWebhookAdapter
from fastapi import FastAPI, Depends, Header, HTTPException, status
import aiohttp

from apraw import Reddit

from .config import config


def auth_dep(authorization:str=Header(...)):
    if authorization != config.authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


app = FastAPI(dependencies=[Depends(auth_dep)])

reddit = Reddit(
    client_id=config.reddit_client_id,
    client_secret=config.reddit_client_secret,
    user_agent="TechStruck",
    username=config.reddit_username,
    password=config.reddit_password
)


REDDIT_ALLOWED_FORMATS = ('.jpg', '.gif', '.png', '.jpeg')
SUBREDDITS = ('memes', 'meme', 'dankmeme', 'me_irl',
              'dankmemes', 'showerthoughts',
              'jokes', 'funny')


async def send_memes(webhook: Webhook, subreddits: List[str], quantity: int):
    sent = 0
    skipped = 0
    while sent < quantity:
        meme_subreddit = await reddit.subreddit(random.choice(SUBREDDITS))
        meme = await meme_subreddit.random()
        if not any((meme.url.endswith(i) for i in REDDIT_ALLOWED_FORMATS)):
            skipped += 1
            continue
        embed = Embed(title=meme.title, color=Color.magenta())
        embed.set_image(url=meme.url)
        embed.set_footer(
            text=f'\U0001f44d {meme.ups} \u2502 \U0001f44e {meme.downs}')
        await webhook.send(embed=embed)
        sent += 1
    return sent, skipped


async def aiohttp_session():
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


@app.get("/meme")
async def send_memes_route(session: aiohttp.ClientSession = Depends(aiohttp_session)):
    sent, skipped = await send_memes(Webhook.from_url(config.meme_webhook_url, adapter=AsyncWebhookAdapter(session)), SUBREDDITS, 5)
    return {'sent': sent, 'skipped': skipped}


@app.get("/git-tip")
async def git_tip(session: aiohttp.ClientSession = Depends(aiohttp_session)):
    tips_json_url = "https://raw.githubusercontent.com/git-tips/tips/master/tips.json"

    async with session.get(tips_json_url) as res:
        tips = json.loads(await res.text())

    tip_no = (datetime.date.today() - datetime.date(2021, 1, 28)).days

    tip = tips[tip_no]

    await Webhook.from_url(config.git_tips_webhook_url, adapter=AsyncWebhookAdapter(session)).send(
        "<@&804403893760688179>",
        embed=Embed(
            title=tip['title'],
            description='```sh\n' + tip['tip'] + '```',
            color=Color.green()
        ).set_footer(text="Tip {}".format(tip_no)),
        avatar_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Git_icon.svg/2000px-Git_icon.svg.png"
    )
    return {"status": "success"}
