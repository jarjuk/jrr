#!/usr/bin/env python

import argparse
import os
import logging
from PIL import Image

from constants import CLI
logger = logging.getLogger(__name__)


def parse_arguments():
    parsed = argparse.ArgumentParser(description='Create icon sprite')
    parsed.add_argument(
        '-i', '--input-directory', help="input directory",
        default=os.path.join(os.path.dirname(
            os.path.realpath(__file__)),  "../resources/sprite")
    )
    parsed.add_argument(
        '-o', '--output-file', help="Output file",
        default=os.path.join(os.path.dirname(
            os.path.realpath(__file__)),  "../tmp/icons-sprite.png")
    )
    parsed.add_argument(
        '--icon-width', type=int, help="Size of icon element in sprite",
        default=CLI.DEFAULT_SPRITE_ICON_SIZE,
    )
    parsed.add_argument(
        '--icon-height', type=int, help="Size of icon element in sprite",
        default=CLI.DEFAULT_SPRITE_ICON_SIZE,
    )
    parsed.add_argument("-v", "--verbose", action="count", default=0)

    return parsed.parse_args()


parser = parse_arguments()



def image_to_thumb(image_path: str,
                   width: int = parser.icon_width,
                   height: int = parser.icon_height,
                   bw: bool = True) -> Image:
    thresh = 100
    display_size = (width, height)
    img = Image.open(image_path)
    if bw:
        def fn(x): return 255 if x > thresh else 0
        thumb_img = img.convert('L').point(fn, mode='1')
    else:
        thumb_img = img
    thumb_img.thumbnail(display_size, Image.Resampling.LANCZOS)
    return thumb_img


def converter(
        input_directory: str,
        parser: argparse.ArgumentParser):

    logger.info("input_directory: %s", input_directory)
    thumbs = []
    for f in sorted(os.listdir(input_directory)):
        image_path = os.path.join(input_directory, f)
        logger.info("image_path: %s", image_path)
        thumb_img = image_to_thumb(image_path=image_path)
        thumbs.append(thumb_img)

    widths, heights = zip(*(i.size for i in thumbs))

    total_width = sum(widths)
    max_height = max(heights)

    sprite = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in thumbs:
      sprite.paste(im, (x_offset,0))
      x_offset += im.size[0]

    logger.info("parser.output_file: %s", parser.output_file)
    sprite.save(parser.output_file)



def main():
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        level=levels[min(parser.verbose, len(levels)-1)],
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
    )
    logger.info("logging.level: %s", logger.level)

    converter(input_directory=parser.input_directory,
              parser=parser)

    print(f"{parser.input_directory=}")


if __name__ == '__main__':
    main()
