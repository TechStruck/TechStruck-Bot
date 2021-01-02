import yaml
from discord import Webhook, RequestsWebhookAdapter, Embed, Color, File
from config import ANNOUNCEMENT_WEBHOOK_URL, BRAINFEED_WEBHOOK_URL, SERVER_ICON_URL


def make_webhook(url: str, adapter=RequestsWebhookAdapter()):
    return Webhook.from_url(url, adapter=adapter)


def yaml_file_to_message(filename: str):
    with open(filename) as f:
        data = yaml.load(f, yaml.Loader)
    message = data.get('message')
    embed_data = data.get('embeds', [])
    file_names = data.get('files', [])

    embeds = []

    for e in embed_data:
        embed = Embed(title=e.get('title'), description=e.get(
            'description'), color=e.get('color', Color.green()))
        for f in e.get('fields', []):
            embed.add_field(name=f['name'], value=f['value'],
                            inline=f.get('inline', False))
        embeds.append(embed)

    return message, embeds, [File(fn) for fn in file_names]


def send_from_yaml(*, webhook: Webhook, filename: str, message: Optional[str] = None, **kwargs):
    msg, embeds, files = yaml_file_to_message(filename)
    return webhook.send(message or msg, files=files, embeds=embeds, **kwargs)
