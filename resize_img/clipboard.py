import win32clipboard as clip
from contextlib import contextmanager


@contextmanager
def open_clipboard():
    try:
        clip.OpenClipboard()
        yield
    finally:
        clip.CloseClipboard()


def current_formats_available():
    with open_clipboard():
        formats = []
        f = 0
        while True:
            f = clip.EnumClipboardFormats(f)
            if f == 0:
                break
            formats.append(f)
        return formats
