"""Module for running image conversion.
"""


import os
from PIL import Image
from urllib.parse import urlparse
from pathlib import Path
import requests
from io import BytesIO

from .config import app_config

import logging
logger = logging.getLogger(__name__)


def load_image(image_url: str):
    """Loads an image from a local file or an HTTP URL."""
    parsed_url = urlparse(image_url)

    if parsed_url.scheme in ("http", "https"):
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    # elif parsed_url.scheme == "file":
    #     local_path = Path(parsed_url.path)
    #     return Image.open(local_path)
    else:
        local_path = Path(parsed_url.path)
        return Image.open(local_path)


def image_resize(
        img: Image.Image,
        width: int,
        height: int,
        bw: bool = False,
) -> Image.Image:
    thresh = 100
    display_size = (width, height)
    if bw:
        def fn(x): return 255 if x > thresh else 0
        img2 = img.convert('L').point(fn, mode='1')
    else:
        img2 = img
    img2.thumbnail(display_size, Image.Resampling.LANCZOS)
    img_resized = Image.new(
        mode='RGB',
        size=display_size,
        color=(255, 255, 255, 0))
    img_resized.paste(img2)
    return img_resized


def image_to_thumb(image_path: str | None = None,
                   img: Image.Image | None = None,
                   thumb_path: str | None = None, 
                   width: int = app_config.streaming_icon_size[0],
                   height: int = app_config.streaming_icon_size[1],
                   bw: bool = True):
    """:image_path: http -url, file-url or filepath to load the image
    from

    TODO: modify to use image_resize

    """
    thresh = 100
    display_size = (width, height)
    # img = Image.open(image_path)
    if img is None and image_path is not None:
        img = load_image(image_path)
    logger.info("image_to_thumb: image_path='%s', thumb_path='%s'",
                image_path, thumb_path)
    if bw and img is not None:
        def fn(x): return 255 if x > thresh else 0
        r = img.convert('L').point(fn, mode='1')
    else:
        r = img
    r.thumbnail(display_size, Image.Resampling.LANCZOS)
    final_thumb = Image.new(
        mode='RGB',
        size=display_size,
        color=(255, 255, 255, 0))
    final_thumb.paste(r)
    final_thumb.save(thumb_path)


# ------------------------------------------------------------------
# Converter main

def converter_main(
        image_dir,
        icon_dir,
        yes,
        width,
        height,
        bw

):
    """
    Convert images to icons suitable for e-paper display.

    Details
    ----


    Parameters
    ----
    :parsed: parsed command line options 


    Return
    -----

    """

    # image_dir = parsed.icons_from
    logger.info("image_dir: %s", image_dir)
    if not os.path.exists(image_dir):
        raise FileExistsError(f"Target path '{image_dir}' does not exist")

    # icon_dir = parsed.icons_to
    logger.info("icon_dir: %s", icon_dir)
    if not os.path.exists(icon_dir):
        raise FileExistsError(f"Target path '{icon_dir}' does not exist")

    logger.info("image_dir: %s", image_dir)
    for f in os.listdir(image_dir):
        image_path = os.path.join(image_dir, f)
        if os.path.isfile(image_path):
            logger.info("image_path: %s", image_path)
            thumb_path = os.path.join(icon_dir, f)
            # if not os.path.exists(thumb_path) or parsed.yes:
            if not os.path.exists(thumb_path) or yes:
                image_to_thumb(image_path=image_path, thumb_path=thumb_path,
                               # width=parsed.width,
                               # height=parsed.height,
                               # bw=parsed.bw
                               width=width,
                               height=height,
                               bw=bw
                               )
                print(f"{thumb_path} - created")
            else:
                print(f"{thumb_path} exists - not overriden")
