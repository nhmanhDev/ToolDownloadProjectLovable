import asyncio
import argparse
import os

from src.api import LovableApi
from src.config import Config, BEARER_TOKEN
from src.builder import source_builder


async def main(url: str, force_overwrite: bool = False):
    # NOTE: async is useless in this context because we are only using a single request
    rootpath = os.path.dirname(os.path.abspath(__file__))
    basedir = os.path.join(
        rootpath,
        "projects",
    )
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    dotenv_path = os.path.join(rootpath, ".env")
    if os.path.exists(dotenv_path):
        import dotenv

        print("Loading environment variables from .env")
        dotenv.load_dotenv(dotenv_path=dotenv_path)

    if not os.environ.get(BEARER_TOKEN):

        print(f"{BEARER_TOKEN} not found.")
        token = input("Paste your Lovable Bearer token: ").strip()
        if not token:
            raise RuntimeError("Bearer token is required to continue")
        print(f"{BEARER_TOKEN} Updated.")
        os.environ[BEARER_TOKEN] = token

    config = Config.from_env()

    async with LovableApi.new(config, lovable_url=url) as api:
        await source_builder(
            basedir=basedir,
            directory_name=api.lovable_uid,
            fetch_source=api.fetch_source,
            force_overwrite=force_overwrite,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone a Lovable project locally (Lovable-style git clone)."
    )
    parser.add_argument(
        "url",
        help="Lovable project URL (e.g. https://lovable.dev/projects/<uuid>)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing directory if it exists.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(url=args.url, force_overwrite=args.force))
