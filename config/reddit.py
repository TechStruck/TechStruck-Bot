from pydantic import BaseSettings
class RedditConfig(BaseSettings):
    client_id: str
    client_secret: str 
    username: str 
    password: str 

    class Config:
        env_file = ".env"
        env_prefix = "reddit_"


reddit_config = RedditConfig()
