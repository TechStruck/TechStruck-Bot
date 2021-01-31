from pydantic import BaseSettings

class StackOAuthConfig(BaseSettings):
    client_id: str
    client_secret: str
    redirect_uri: str
    key: str

    class Config:
        env_file = ".env"
        env_prefix = "stackexchange_"


class GithubOAuthConfig(BaseSettings):
    client_id: str
    client_secret: str
    redirect_uri: str

    class Config:
        env_file = ".env"
        env_prefix = "github_"


stack_oauth_config = StackOAuthConfig()
github_oauth_config = GithubOAuthConfig()
