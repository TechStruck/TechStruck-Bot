from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):

    secret: str
    database_uri: PostgresDsn
    no_ssl: bool = False

    class Config:
        env_file = ".env"
        fields = {
            "database_uri": {"env": ["database_uri", "database_url", "database"]},
            "no_ssl": {"env": "database_no_ssl"},
            "secret": {"env": "signing_secret"},
        }


config = Settings()
