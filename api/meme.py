import json
import random
import traceback
from http.server import BaseHTTPRequestHandler
from typing import List

from discord import Color, Embed, Webhook
from praw import Reddit

from config import config
from utils.webhook import make_webhook

reddit = Reddit(
    client_id=config['REDDIT_ID'],
    client_secret=config['REDDIT_SECRET'],
    user_agent="TechStruck",
    username=config["REDDIT_USERNAME"],
    password=["REDDIT_PASSWORD"]
)

reddit.read_only = True


webhook = make_webhook(config['MEME_CHANNEL_WEBHOOK_URL'])

ALLOWED_FORMATS = ('.jpg', '.gif', '.png', '.jpeg')
SUBREDDITS = ('memes', 'meme', 'dankmeme', 'me_irl',
              'dankmemes', 'blursedimages', 'showerthoughts',
              'jokes', 'funny')


def send_memes(webhook: Webhook, subreddits: List[str], quantity: int):
    sent = 0
    skipped = 0
    while sent < quantity:
        meme_subreddit = reddit.subreddit(random.choice(SUBREDDITS))
        meme = meme_subreddit.random()
        if not any((meme.url.endswith(i) for i in ALLOWED_FORMATS)):
            skipped += 1
            continue
        embed = Embed(title=meme.title, color=Color.magenta())
        embed.set_image(url=meme.url)
        embed.set_footer(
            text=f'\U0001f44d {meme.ups} \u2502 \U0001f44e {meme.downs}')
        webhook.send(embed=embed)
        sent += 1
    return {'sent': sent, 'skipped': skipped}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):

        try:
            out = send_memes(webhook, SUBREDDITS, 5)
        except Exception as e:
            self.send_response(500)
            out = {'error': traceback.format_exception(
                type(e), e, e.__traceback__)}
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

        self.wfile.write(json.dumps(out).encode())
