from aiohttp import ClientSession
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from .config import Config

from typing import Sequence, MutableMapping, Any

type JSON = None | str | bool | int | float | Sequence[JSON] | MutableMapping[str, JSON]


class Session:
    http_session: ClientSession

    def __init__(self) -> None:
        raise ValueError("please use .new")

    @classmethod
    @asynccontextmanager
    async def new(cls, config: Config):
        headers = {
            "UserAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "accept-language": "en-US,en;q=0.7",
            "accept-encoding": "gzip, deflate",
            "accept": "*/*",
            "priority": "u=1, i",
            "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "sec-gpc": "1",
            "authorization": config.bearer_token,
        }
        if not config.aiohttp_cache_dir:
            async with ClientSession(headers=headers) as http_session:
                self = cls.__new__(cls)
                self.http_session = http_session
                yield self
        else:
            from aiohttp_client_cache.session import CachedSession
            from aiohttp_client_cache.backends.base import CacheBackend
            from aiohttp_client_cache.backends.sqlite import SQLiteBackend
            from datetime import timedelta

            cache_backend: CacheBackend = SQLiteBackend(
                cache_name=config.aiohttp_cache_dir,
                use_temp=False,
                fast_save=False,
                autoclose=True,
                expire_after=timedelta(days=1),
                allowed_codes=(200,),
                allowed_methods=("GET", "HEAD"),
            )

            async with CachedSession(
                cache=cache_backend, headers=headers
            ) as http_session:
                self = cls.__new__(cls)
                self.http_session = http_session
                yield self

    @asynccontextmanager
    async def request(
        self,
        method: str,
        url: str,
        json: JSON = None,
        data: Any = None,
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
    ):
        parsed = urlparse(url)
        domain = parsed.netloc

        host_parts = domain.split(".")
        root_domain = ".".join(host_parts[-2:])

        async with self.http_session.request(
            method=method,
            url=url,
            json=json,
            data=data,
            cookies=cookies,
            headers={
                "authority": domain,
                "origin": f"{parsed.scheme}://{root_domain}",
                "referer": f"{parsed.scheme}://{root_domain}",
                **headers,
            },
        ) as resp:
            yield resp
