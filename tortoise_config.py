from config import common
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

database_uri = common.config.database_uri

tortoise_config = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
            "database": database_uri.path[1:],
            "host": database_uri.host,
            "password": database_uri.password,
            "port": database_uri.port or 5432,
            "user": database_uri.user,
            "ssl": ctx
        }
    }
    },
    "apps": {
        "main": {
            "models": ["models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
