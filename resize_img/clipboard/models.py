import struct
from typing import Any, NamedTuple
from enum import Flag


class ClipboardFormat(NamedTuple):
    name: str
    number: int
    type: str
    content: Any

    def __repr__(self):
        name, number, type = self.name, self.number, self.type
        return f"ClipboardFormat({name=}, {number=}, {type=})"

    def __str__(self):
        return self.__repr__()


class PreferredDropEffect(Flag):
    NONE = 0
    COPY = 1
    MOVE = 2
    LINK = 4
    DROPEFFECT_SCROLL = 2147483648

    @classmethod
    def from_bytes(cls, val: bytes):
        return cls(struct.unpack("l", val)[0])
