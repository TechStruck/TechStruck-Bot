import yaml
from discord import Embed, Color, File


def build_embed(embed_data):
    embed = Embed(title=embed_data.get('title'), description=embed_data.get(
        'description'), color=embed_data.get('color', Color.green()))

    if 'thumbnail' in embed_data:
        embed.set_thumbnail(url=embed_data['thumbnail'])

    if 'image' in embed_data:
        embed.set_image(url=embed_data['image'])

    for f in embed_data.get('fields', []):
        embed.add_field(name=f['name'], value=f['value'],
                        inline=f.get('inline', False))

    return embed


def bot_type_converter(data):
    text = data.get('text')
    embed_data = data.get('embed')
    file_names = data.get('files', [])

    embed = None

    if embed_data:
        embed = build_embed(embed_data)

    return text, embed, [File(fn) for fn in file_names]


def webhook_type_converter(data):
    messages_data = data
    outputs = []
    for message_data in messages_data.get('messages', []):
        embeds_data = message_data.get('embeds', [])
        embeds = [build_embed(embed_data) for embed_data in embeds_data]
        outputs.append((message_data.get('text'), embeds, [File(
            fn) for fn in message_data.get('files', [])] or None))

    return outputs, messages_data.get('username'), messages_data.get('avatar_url')


def yaml_file_to_message(filename: str):
    with open(filename) as f:
        data = yaml.load(f, yaml.Loader)
    if data['type'] == 'bot':
        return bot_type_converter(data)
    if data['type'] == 'webhook':
        return webhook_type_converter(data)
    raise RuntimeError("Incompatible type")
