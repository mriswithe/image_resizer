from contextlib import contextmanager
import imghdr
import logging
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageGrab

from .notify import notify_completed, notify_no_changes, notify_too_many_files

MAX_SIZE = 8 * 2 ** 20
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


@contextmanager
def temp_image_file(image: Image.Image, **kwargs) -> BytesIO:
    f = kwargs.pop('format', image.k)
    with BytesIO() as fp:
        image.save(fp, format=f, **kwargs)
        fp.seek(0)
        yield fp


@contextmanager
def optimize_only(image: Image.Image):
    with temp_image_file(image, optimize=True) as fp:
        yield fp


def resize_image(img: Image.Image, percent_reduction: float):
    pass


def send_to_clipboard(fp):
    pass


def check_size(fp) -> int:
    fp.seek(0)
    size = len(fp.read())
    fp.seek(0)
    return size


def process_image(image: Image.Image):
    with temp_image_file(image) as fp:
        img_size = len(fp.read())
    LOGGER.info(f"Starting image size: {img_size:,} bytes")
    if img_size <= MAX_SIZE:
        LOGGER.info(f"Image is already under the goal size")
        return
    else:
        with optimize_only(image) as fp:
            LOGGER.info(f'Saving with optimize')
            new_size = len(fp.read())
            LOGGER.info(f'Optimized is {img_size:,} bytes')
            if new_size <= MAX_SIZE:
                LOGGER.info('Optimized without resize achieved goal size.')
                send_to_clipboard(fp)
                return
        # We haven't shrunk the image enough yet
        size = float('infinity')
        next_percent = 90
        while size > MAX_SIZE:
            file, size = resize_image(image, next_percent)


def filter_paths_to_images(file_list: list[str]) -> list[Path]:
    # Check that paths are images with imghdr
    file_list: list[str] = list(filter(imghdr.what, file_list))
    # Make them pathlib paths
    file_list: list[Path] = list(map(Path, file_list))
    return file_list


def main():
    if not (image := ImageGrab.grabclipboard()):
        # Handles not having image data or file paths on clipboard
        return
    elif isinstance(image, list):
        # Handles list of files
        if list_size := len(file_paths := filter_paths_to_images(image)) == 0:
            LOGGER.info(f"No image files files on clipboard -- Exiting")
            return
        elif list_size == 1:
            LOGGER.info(f"File path on clipboard being used as source image")
            process_image(Image.open(file_paths[0]))
        elif list_size > 1:
            LOGGER.info(f"Can't handle multiple image paths on clipboard! -- Exiting")
    else:
        # Handles image data on clipboard
        LOGGER.info(f"")
        process_image(image)


if __name__ == '__main__':
    main()
