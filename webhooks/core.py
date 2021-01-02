from discord import Webhook, RequestsWebhookAdapter, Embed, Color
from config import ANNOUNCEMENT_WEBHOOK_URL, BRAINFEED_WEBHOOK_URL, SERVER_ICON_URL


def make_webhook(url: str, adapter=RequestsWebhookAdapter):
    return Webhook.from_url(url, adapter=adapter)
