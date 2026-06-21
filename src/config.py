from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

BEARER_TOKEN: str = "BEARER_TOKEN"

class Config(BaseSettings):
    bearer_token: str = Field(..., alias=BEARER_TOKEN)
    aiohttp_cache_dir: str | None = Field(None, alias="AIOHTTP_CACHE_DIR")
    lovable_valid_domain: str = Field(
        default="lovable.dev",
        alias="LOVABLE_VALID_DOMAIN",
        min_length=1,
        description="The domain of the Lovable platform. Default is 'lovable.dev'.",
    )

    @field_validator("bearer_token")
    @classmethod
    def ensure_bearer_prefix(cls, v: str) -> str:
        v = v.strip()
        if not v.lower().startswith("bearer "):
            return f"Bearer {v}"
        return v

    @classmethod
    def from_env(cls):
        self = cls()  # pyright: ignore[reportCallIssue]
        return self

    @classmethod
    def from_dotenv(cls, dotenv_path: str | None = None):
        import dotenv

        dotenv.load_dotenv(dotenv_path=dotenv_path)
        return cls.from_env()
