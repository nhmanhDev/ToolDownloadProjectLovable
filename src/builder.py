from .model import SourceFiles
from typing import Callable, Awaitable
import os


async def source_builder(basedir: str, directory_name: str, fetch_source: Callable[[], Awaitable[SourceFiles]], force_overwrite: bool = False):
    if not os.path.exists(basedir):
        raise ValueError(f"Base directory {basedir} does not exist")
    directory_path = os.path.join(basedir, directory_name)
    if not os.path.exists(directory_path):
        os.mkdir(directory_path)
    elif not force_overwrite:
        raise ValueError(
            f"Directory {directory_name} already exists in base directory {basedir}"
            " and overwrite is set to False. Use `force_overwrite=True` to overwrite the directory."
        )
    source = await fetch_source()
    for file in source.files:
        data = file.get_data()
        if data is None:
            print(f"Skipping file `{directory_name}/{file.name}` as it has no data")
            continue

        file_path = os.path.join(directory_path, file.name)
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "wb") as f:
            f.write(data)
