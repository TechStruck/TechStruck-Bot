from pydantic import BaseSettings


class BotConfig(BaseSettings):
    bot_token: str
    quiz_api_token: str
    pastebin_api_key: str

    class Config:
        env_file = ".env"


bot_config = BotConfig()
