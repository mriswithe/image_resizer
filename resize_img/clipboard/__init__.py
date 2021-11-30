import inspect
from contextlib import contextmanager
from io import BytesIO

import pywintypes
import win32clipboard
from PIL.Image import Image

from .models import ClipboardFormat, PreferredDropEffect

STANDARD_FORMATS = {
    c[1]: c[0]
    for c in inspect.getmembers(win32clipboard)
    if c[0].startswith("CF_") and isinstance(c[1], int)
}

# Ref https://docs.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats
# for the ranges involved
GDI_OBJ_FIRST = 0x0300
GDI_OBJ_LAST = 0x3FF
PRIV_FIRST = 0x0200
PRIV_LAST = 0x02FF


@contextmanager
def open_clipboard():
    try:
        win32clipboard.OpenClipboard()
        yield
    finally:
        win32clipboard.CloseClipboard()


def current_formats_available():
    with open_clipboard():
        formats = []
        f = 0
        while True:
            f = win32clipboard.EnumClipboardFormats(f)
            if f == 0:
                break
            else:
                if name := STANDARD_FORMATS.get(f):
                    format_type = "STANDARD"
                else:
                    name = win32clipboard.GetClipboardFormatName(f)
                    if PRIV_FIRST < f < PRIV_LAST:
                        format_type = "PRIVATE"
                    elif GDI_OBJ_FIRST < f < GDI_OBJ_LAST:
                        format_type = "GDI_OBJ"
                    else:
                        format_type = "CUSTOM"
                # noinspection PyUnresolvedReferences
                try:
                    content = win32clipboard.GetClipboardData(f)
                except pywintypes.error as e:
                    print(f"Unable to get content for format {name} ({f})")
                    content = "UNAVAILABLE"
                if name.lower() == "Preferred DropEffect".lower():
                    content = PreferredDropEffect.from_bytes(content)
                formats.append(ClipboardFormat(name, f, format_type, content))
        return formats


def get_bmp_data(img: Image) -> bytes:
    """Returning after the first 14 bytes as that is what CF_DIB expects"""
    with BytesIO() as b:
        img.save(b, "BMP")
        b.seek(0)
        return b.read()[14:]


def get_png_data(img: Image) -> bytes:
    """Returning the whole content of the file as that is what seems to be the
    undocumented standard for PNG types on the windows clipboard"""
    with BytesIO() as b:
        img.save(b, "PNG")
        b.seek(0)
        return b.read()


def write_to_clipboard(img: Image, png_data: bytes = None, bmp_data: bytes = None):
    if not bmp_data:
        bmp_data = get_bmp_data(img)
    if not png_data:
        png_data = get_png_data(img)
    png_format_number = win32clipboard.RegisterClipboardFormat("PNG")
    preferred_dropeffect_number = win32clipboard.RegisterClipboardFormat(
        "Preferred DropEffect"
    )
    copy_bytes = PreferredDropEffect.COPY.to_bytes()
    print(copy_bytes)
    with open_clipboard():
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.SetClipboardData(png_format_number, png_data)
        win32clipboard.SetClipboardData(
            preferred_dropeffect_number, PreferredDropEffect.COPY.to_bytes()
        )
