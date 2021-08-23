import imghdr
import logging
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageGrab

from .clipboard import write_to_clipboard
from .notify import notify_completed, notify_no_changes, notify_too_many_files

MAX_SIZE = 8 * 2 ** 20
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


@contextmanager
def temp_image_file(image: Image.Image, **kwargs) -> BytesIO:
    try:
        f = kwargs.pop("format", image.k)
    except AttributeError:
        LOGGER.debug(f"Using PNG as a fallback format")
        f = "png"
    with BytesIO() as fp:
        image.save(fp, format=f, **kwargs)
        fp.seek(0)
        yield fp


@contextmanager
def optimize_only(image: Image.Image) -> BytesIO:
    with temp_image_file(image, optimize=True) as fp:
        yield fp


def resize_image(img: Image.Image, percent_reduction: float) -> Image.Image:
    return img.resize(reduced_size(img, percent_reduction))


def reduced_size(img: Image.Image, percent_reduction: float) -> tuple[int, int]:
    return int(img.width * percent_reduction), int(img.height * percent_reduction)


def check_size(img: Image.Image) -> tuple[int, bytes]:
    with temp_image_file(img) as fp:
        fp.seek(0)
        data = fp.read()
        size = len(data)
    return size, data


def process_image(image: Image.Image):
    img_size = check_size(image)
    LOGGER.info(f"Starting image size: {img_size:,} bytes")
    if img_size <= MAX_SIZE:
        LOGGER.info(f"Image is already under the goal size")
        return
    else:
        LOGGER.info(f"Saving with optimize")
        with optimize_only(image) as fp:
            data = fp.read()
            new_size = len(data)
            LOGGER.info(f"Optimized is {img_size:,} bytes")
            if new_size <= MAX_SIZE:
                LOGGER.info("Optimized without resize achieved goal size.")
                write_to_clipboard(image, png_data=data)
                return
        # We haven't shrunk the image enough yet
        size = float("infinity")
        next_percent = 0.9
        while size > MAX_SIZE:
            new_image = resize_image(image, next_percent)
            size, data = check_size(new_image)
            LOGGER.info(f"Image at {size:,} bytes at {next_percent:.2%}")
            if size > MAX_SIZE:
                next_percent -= 0.1
            else:
                write_to_clipboard(new_image, png_data=data)


def filter_paths_to_images(file_list: list[str]) -> list[Path]:
    # Check that paths are images with imghdr
    file_list: list[str] = list(filter(imghdr.what, file_list))
    # Make them pathlib paths
    file_list: list[Path] = list(map(Path, file_list))
    return file_list


def main():
    if not (image := ImageGrab.grabclipboard()):
        # Handles not having image data or file paths on clipboard
        logging.info(f"No image data or file paths on clipboard. Exiting.")
        return
    elif isinstance(image, list):
        # Handles list of files
        if (list_size := len(file_paths := filter_paths_to_images(image))) == 0:
            LOGGER.info(f"No image files files on clipboard -- Exiting")
            return
        elif list_size == 1:
            LOGGER.info(f"File path on clipboard being used as source image")
            process_image(Image.open(file_paths[0]))
        elif list_size > 1:
            LOGGER.info(f"Can't handle multiple image paths on clipboard! -- Exiting")
    else:
        # Handles image data on clipboard
        LOGGER.info(f"Processing image on clipboard")
        process_image(image)


if __name__ == "__main__":
    main()
