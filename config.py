import os
import yaml

try:
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.Loader)
except FileNotFoundError:
    config = {}

config.update(os.environ)

tortoise_config = {
    "connections": {"default": config['DATABASE_URL']},
    "apps": {
        "main": {
            "models": ["bot.models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
