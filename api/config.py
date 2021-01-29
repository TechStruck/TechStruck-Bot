from pydantic import BaseSettings


class Settings(BaseSettings):
    git_tips_webhook_url: str
    meme_webhook_url: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_username: str
    reddit_password: str

    authorization: str

    class Config:
        env_file = ".env"


config = Settings()
