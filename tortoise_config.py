from config import config
tortoise_config = {
    "connections": {"default": config['DATABASE_URL']},
    "apps": {
        "main": {
            "models": ["bot.models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
