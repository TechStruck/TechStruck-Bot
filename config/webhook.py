from pydantic import BaseSettings


class Webhooks(BaseSettings):
    git_tips: str
    meme: str
    authorization: str

    class Config:
        env_file = ".env"
        env_prefix = "webhook_url_"
        fields = {'authorization': {'env': 'authorization'}}


webhook_config = Webhooks()
