from config import common
tortoise_config = {
    "connections": {"default": common.config.database_uri},
    "apps": {
        "main": {
            "models": ["models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
