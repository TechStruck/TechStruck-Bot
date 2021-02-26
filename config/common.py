from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):

    secret: str
    database_uri: PostgresDsn

    class Config:
        env_file = ".env"
        fields = {
            "database_uri": {"env": ["database_uri", "database_url", "database"]},
            "secret": {"env": "signing_secret"},
        }


config = Settings()
