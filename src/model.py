from pydantic import BaseModel, model_validator
from typing import cast
import base64


class SourceFile(BaseModel):
    name: str
    binary: bool
    sizeExceeded: bool
    contents: str | None = None

    @model_validator(mode="after")
    def check_contents_when_size_exceeded(self):
        if self.sizeExceeded and self.contents is not None:
            raise ValueError("contents must be None when sizeExceeded is True")
        if not self.sizeExceeded and self.contents is None:
            raise ValueError("contents can be None only when sizeExceeded is True")
        return self

   
    def get_data(self) -> bytes | None:
        if self.sizeExceeded:
            return None
        contents = cast(str, self.contents)
        if self.binary:
            return base64.b64decode(contents)
        else:
            return contents.encode("utf-8")


class SourceFiles(BaseModel):
    files: list[SourceFile]
