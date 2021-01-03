from discord import Webhook, RequestsWebhookAdapter
from typing import Optional
from .embed import yaml_file_to_message


def make_webhook(url: str, adapter=RequestsWebhookAdapter()):
    return Webhook.from_url(url, adapter=adapter)


def send_from_yaml(*, webhook: Webhook, filename: str, text: Optional[str] = None, **kwargs):
    messages, username, avatar_url = yaml_file_to_message(filename)
    kwargs.setdefault('username', username)
    kwargs.setdefault('avatar_url', avatar_url)
    return [webhook.send(message[0] or text,  embeds=message[1], files=message[2], **kwargs) for message in messages]
