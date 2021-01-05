from http.server import BaseHTTPRequestHandler
from praw import Reddit
from utils.webhook import make_webhook
from discord import Embed, Color
from config import config

reddit = Reddit(
    client_id=config['REDDIT_ID'],
    client_secret=config['REDDIT_SECRET'],
    user_agent="TechStruck",
    username=config["REDDIT_USERNAME"],
    password=["REDDIT_PASSWORD"]
)

reddit.read_only = True


webhook = make_webhook(config['MEME_CHANNEL_WEBHOOK_URL'])


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        sent = 0
        while sent < 5:
            meme_subreddit = reddit.subreddit(random.choice(
                ('memes', 'MemeEconomy', 'dankmemes', 'dankmemer')))
            meme = meme_subreddit.random()
            if not any((meme.url.endswith(i) for i in ('.jpg', '.gif', '.png', '.jpeg'))):
                continue
            embed = Embed(title=meme.title, color=Color.greyple())
            embed.set_image(url=meme.url)
            embed.set_footer(
                text=f'\U0001f44d {meme.ups} \u2502 \U0001f44e {meme.downs}')
            webhook.send(embed=embed)
            sent += 1

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        self.wfile.write("Done".encode())
