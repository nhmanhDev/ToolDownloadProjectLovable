from .core import Session
from .config import Config
from .model import SourceFiles

from contextlib import asynccontextmanager
from urllib.parse import ParseResult, urlparse


class LovableApi:
    session: Session
    lovable_url: ParseResult  # eg: https://lovable.dev/projects/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    lovable_uid: str  # eg: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def __init__(self) -> None:
        raise ValueError("please use .new")

    @classmethod
    @asynccontextmanager
    async def new(cls, config: Config, lovable_url: str):
        parsed = urlparse(lovable_url)
        if parsed.netloc != config.lovable_valid_domain:
            raise ValueError(
                f"{parsed.netloc} is not a valid Lovable domain. Please use {config.lovable_valid_domain} instead"
            )
        if not parsed.path.startswith("/projects/"):
            raise ValueError(
                f"{lovable_url} must be like `https://lovable.dev/projects/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`"
            )
        uid = parsed.path.removeprefix("/projects/").removesuffix("/")
        if not len(uid) == 36 or not uid.count("-") == 4:
            raise ValueError(
                f"{lovable_url} must be like `https://lovable.dev/projects/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`"
            )
        async with Session.new(config) as session:
            self = cls.__new__(cls)
            self.session = session
            self.lovable_url = parsed
            self.lovable_uid = uid
            yield self

    async def fetch_source(self) -> SourceFiles:
        domain = self.lovable_url.netloc

        slash = "" if self.lovable_url.path.endswith("/") else "/"

        async with self.session.request(
            "GET",
            f"{self.lovable_url.scheme}://api.{domain}{self.lovable_url.path}{slash}source-code",
        ) as resp:
            resp.raise_for_status()
            return SourceFiles.model_validate(await resp.json())
