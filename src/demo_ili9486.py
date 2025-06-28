#!/usr/bin/env python3
"""Demo display functions on ILI9484 TFT 3.5 inch display
"""

import argparse
import os
import sys
from PIL import Image, ImageFont, ImageDraw
import RPi.GPIO as GPIO
from spidev import SpiDev
import time
import logging
import asyncio
from collections import deque

from constants import RPI
from Python_ILI9486 import ILI9486 as LCD
from tft_ili9486 import TFT_DRIVER

# ------------------------------------------------------------------
# module state
logger = logging.getLogger(__name__)


def init_lcd():
    GPIO.setmode(GPIO.BCM)

    spi = SpiDev(RPI.ILI9486.SPI_BUS, RPI.ILI9486.SPI_DEVICE)
    spi.mode = 0b10  # [CPOL|CPHA] -> polarity 1, phase 0
    # default value
    # spi.lsbfirst = False  # set to MSB_FIRST / most significant bit first
    spi.max_speed_hz = 64000000
    logger.info("DC_PIN=%s, rst=%s",
                RPI.ILI9486.DC_PIN, RPI.ILI9486.RST_PIN)
    lcd = LCD.ILI9486(dc=RPI.ILI9486.DC_PIN,
                      rst=RPI.ILI9486.RST_PIN, spi=spi).begin()
    return lcd


def close_lcd(lcd: LCD):
    print('Turning on idle mode')
    lcd.idle()
    print('Clearing display')
    lcd.clear().display()
    print('Resetting display')
    lcd.begin()
    print('Turning on sleep mode')
    lcd.sleep()
    print('Turning off sleep mode')
    lcd.wake_up()


def demo_sleep(lcd: LCD, text: str, count: int = 5, sleep_time: float = 0.1):
    logger.info("text: %s", text)
    # Draw some text on the image
    logger.info("lcd.dimensions(): %s", lcd.dimensions())

    # Font
    picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)

    # Find size of text block
    image_text = Image.new("RGB", lcd.dimensions(), "white")
    draw_text = ImageDraw.Draw(image_text)
    bbox = draw_text.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    # text_x = (width - text_width) // 2
    # text_y = (height - text_height) // 2

    for i in range(count):

        text_dimensions = (text_width, text_height)
        image_text = Image.new("RGB", text_dimensions, "white")
        draw_text = ImageDraw.Draw(image_text)

        text_x = 0
        text_y = 0
        draw_text.text((text_x, text_y), text, font=font, fill="black")
        # image = Image.new("RGB", lcd.dimensions(), "white")

        if i == 0:
            logger.info("start-nop: i='%s'", i)

        elif i == 1:
            logger.info("clear w.display: i='%s'", i)
            lcd.clear()
            lcd.display()
            # img_black = Image.new("RGB", lcd.dimensions(), "black")
            # lcd.display(img_black)
            logger.info("sleep time: i='%s'", i)
            time.sleep(sleep_time)
            logger.info("wakeup, i='%s'", i)

        elif i == 2:
            logger.info("clear & sleep: i='%s'", i)
            lcd.clear()
            lcd.sleep()

        elif i == 3:
            logger.info("no-op: i='%s'", i)

        elif i == 4:
            logger.info("wake_up: i='%s'", i)
            lcd.wake_up()

        elif i == 5:
            logger.info("no-op: i='%s'", i)

        elif i == 6:
            logger.info("off: i='%s'", i)
            lcd.off()

        elif i == 7:
            logger.info("nop: i='%s'", i)

        elif i == 8:
            logger.info("on: i='%s'", i)
            lcd.on()

        width, height = lcd.dimensions()
        # text_width, text_height = draw.textsize(text, font=font)
        # text_width, text_height = font.getsize(text)
        lcd.display(image_text, y0=i*20)
        time.sleep(sleep_time)


def demo_text(lcd: LCD, text: str, count: int = 5, sleep_time: float = 0.0, line_space=4):
    logger.info("text: %s", text)
    # Draw some text on the image
    logger.info("lcd.dimensions(): %s", lcd.dimensions())

    # Font
    picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)

    # Find size of text block
    line_image = Image.new("RGB", lcd.dimensions(), "white")
    logger.info(": lcd.dimensions()='%s'", lcd.dimensions())
    line_draw = ImageDraw.Draw(line_image)
    bbox = line_draw.textbbox((0, 0), text, font=font)
    # text_width = bbox[2] - bbox[0]
    line_width = lcd.dimensions()[0] - bbox[0]
    line_height = bbox[3] - bbox[1] + line_space
    line_step = line_height
    logger.info(": line (w,h)=(%s,%s), line_step: %s",
                line_width, line_height, line_step)
    # text_x = (width - text_width) // 2
    # text_y = (height - text_height) // 2

    for i in range(count):

        text_dimensions = (line_width, line_height)
        line_image = Image.new("RGB", text_dimensions, "white")
        line_draw = ImageDraw.Draw(line_image)

        text_x = 0
        text_y = 0
        # line_draw.text((text_x, text_y), text, font=font, fill="black")
        # image = Image.new("RGB", lcd.dimensions(), "white")
        line_draw.text((text_x, text_y), f"{i}:{text}",
                       font=font, fill=True, anchor='lt')

        # width, height = lcd.dimensions()
        # text_width, text_height = draw.textsize(text, font=font)
        # text_width, text_height = font.getsize(text)
        lcd.display(line_image, y0=i*line_step)
        time.sleep(sleep_time)


async def demo_driver(driver: TFT_DRIVER, image_path: str):
    await asyncio.sleep(1)
    image = Image.open(image_path)
    partial = image.resize((driver.width, driver.height))
    await driver.display(image=image)
    print("done")


def demo_image(lcd: LCD, image_path: str):
    image = Image.open(image_path)
    width, height = image.size
    partial = image.resize((width // 2, height // 2))
    for i in range(2):
        print('Drawing image')
        lcd.display(image)
        time.sleep(1)
        print('Drawing partial image')
        lcd.display(partial)
        time.sleep(1)
        print('Turning on inverted mode')
        lcd.invert()
        time.sleep(1)
        print('Turning off inverted mode')
        lcd.invert(False)
        time.sleep(1)
        print('Turning off display')
        lcd.off()
        time.sleep(1)
        print('Turning on display')
        lcd.on()
        time.sleep(1)
        print('Turning on idle mode')
        lcd.idle()
        time.sleep(1)
        print('Turning off idle mode')
        lcd.idle(False)
        time.sleep(1)
        print('Clearing display')
        lcd.clear().display()
        time.sleep(1)
        print('Resetting display')
        lcd.begin()
        time.sleep(1)
        print('Turning on sleep mode')
        lcd.sleep()
        time.sleep(1)
        print('Turning off sleep mode')
        lcd.wake_up()
        time.sleep(1)

# ------------------------------------------------------------------
# Command line arguments

# https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output


class _HelpAction(argparse._HelpAction):
    """Sub parser helps"""

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print(f"Command '{choice}'")
                print(subparser.format_help())

        parser.exit()


def commandLineParser() -> argparse.ArgumentParser:
    """Return command line parser.

    laturi [options] [command]

    Options:

    -v                : versbosity

    Commands:

    kan1              : the simples kan model
    """

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--verbose", action="count", default=1)
    parser.add_argument('--help', action=_HelpAction,
                        help='help for help if you need some help')
    subparsers = parser.add_subparsers(help='Commands', dest="command")

    demo_image_parser = subparsers.add_parser(
        "demo-image", help="Demo image")
    demo_image_parser.add_argument(
        "--image", type=str, default="Python_ILI9486/sample.png",
        help=f"Image to demo",
    )

    demo_image_parser = subparsers.add_parser(
        "demo-driver", help="Demo image using driver")
    demo_image_parser.add_argument(
        "--image", type=str, default="Python_ILI9486/sample.png",
        help=f"Image to demo",
    )
    
    demo_close_parser = subparsers.add_parser(
        "close", help="Close LCD")

    demo_text_parser = subparsers.add_parser(
        "demo-text", help="Demo text")

    demo_text_parser.add_argument(
        "--text", type=str, default="Hello World",
        help=f"Text to demo",
    )
    demo_text_parser.add_argument(
        "--count", type=int, default=10,
        help=f"Number of count",
    )

    demo_sleep_parser = subparsers.add_parser(
        "demo-sleep", help="Demo sleep")

    demo_sleep_parser.add_argument(
        "--text", type=str, default="Hello World",
        help=f"Text to demo",
    )
    demo_sleep_parser.add_argument(
        "--sleep-time", type=float, default=5.0,
        help=f"Time to sleep",
    )
    demo_sleep_parser.add_argument(
        "--count", type=int, default=10,
        help=f"Number of count",
    )

    demo_pipe_parser = subparsers.add_parser(
        "pipe", help="Pipe stdin to LCD")

    return parser


def commandLineArgruments(args):
    """Process command line argurments"""
    parser = commandLineParser()
    parsed_args = parser.parse_args(args)

    return parsed_args


def pipe_stdin(lcd: LCD, max_lines: int | None = None):
    """

    """

    font_size = 10
    line_height = font_size + 2
    line_width = lcd.dimensions()[0]
    line_step = line_height
    if max_lines is None:
        max_lines = lcd.dimensions()[1]/line_height

    # Font
    picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), font_size)

    # Find size of text block
    line_image = Image.new("RGB", lcd.dimensions(), "white")
    logger.info(": lcd.dimensions()='%s'", lcd.dimensions())


    lines: deque = deque([])
    for line in sys.stdin:
        lines.append(line.rstrip())
        if len(lines) > max_lines:
            lines.popleft()

        logger.debug("pipe_stdin: var='%s'", line)

        for i in range(len(lines)):

            text_dimensions = (line_width, line_height)
            line_image = Image.new("RGB", text_dimensions, "white")
            line_draw = ImageDraw.Draw(line_image)

            text_x = 0
            text_y = 0
            line_draw.text((text_x, text_y), f"{i}:{lines[i]}",
                           font=font, fill=True, anchor='lt')

            # width, height = lcd.dimensions()
            # text_width, text_height = draw.textsize(text, font=font)
            # text_width, text_height = font.getsize(text)
            lcd.display(line_image, y0=i*line_step)


# ------------------------------------------------------------------
# Main


def main(args):
    parsed = commandLineArgruments(args)
    # Set output log level
    # logging.basicConfig(level=logging.DEBUG)
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        level=levels[min(parsed.verbose, len(levels)-1)],
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
    )
    logger.info("logging.level: %s", logger.level)
    if parsed.command == "demo-image":
        lcd = init_lcd()
        try:
            demo_image(
                lcd=lcd,
                image_path=parsed.image
            )

        finally:
            close_lcd(lcd)
    elif parsed.command == "demo-driver":
        driver = TFT_DRIVER(dc=RPI.ILI9486.DC_PIN,
                            spi_bus=RPI.ILI9486.SPI_BUS,
                            spi_device=RPI.ILI9486.SPI_DEVICE,
                            rst=RPI.ILI9486.RST_PIN, )
        try:
            asyncio.run(
                demo_driver(
                    driver=driver,
                    image_path=parsed.image,
                ))
        finally:
            driver.module_exit()
    elif parsed.command == "demo-text":
        lcd = init_lcd()
        try:
            demo_text(
                lcd=lcd,
                text=parsed.text,
                count=parsed.count,
            )
        finally:
            time.sleep(2)
            input("Press RET")
            close_lcd(lcd)
    elif parsed.command == "close":
        lcd = init_lcd()
        close_lcd(lcd)
    elif parsed.command == "demo-sleep":
        lcd = init_lcd()
        try:
            demo_sleep(
                lcd=lcd,
                text=parsed.text,
                count=parsed.count,
                sleep_time=parsed.sleep_time,
            )
        finally:
            time.sleep(2)
            close_lcd(lcd)
    elif parsed.command == "pipe":
        logger.info("main:: parsed.command='%s'", parsed.command)
        lcd = None
        while lcd is None:
            try:
                lcd = init_lcd()
            except Exception as e:
                logger.warning("Could not get lcd: e='%s'", e)
                time.sleep(2)
        try:
            logger.info("main: enter pipe_stdin lcd='%s'", lcd)
            pipe_stdin(
                lcd=lcd,
            )
        finally:
            close_lcd(lcd)
        logger.info("main: Exiting")

    else:
        logger.error(f"No command found '{parsed.command=}'")
        raise NotImplementedError


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
