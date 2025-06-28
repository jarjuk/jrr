"""Services for using TFT display as console.
"""

import platform
import re
import os
import io
import subprocess
from spidev import SpiDev
import RPi.GPIO as GPIO
from PIL import Image, ImageFont, ImageDraw
from collections import deque

from .Python_ILI9486 import ILI9486 as LCD
from .constants import RPI

import logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Module state

lcd: LCD.ILI9486 | None = None


# ------------------------------------------------------------------
#
def init_lcd():
    """Init LCD"""
    GPIO.setmode(GPIO.BCM)

    spi = SpiDev(RPI.ILI9486.SPI_BUS, RPI.ILI9486.SPI_DEVICE)
    spi.mode = 0b10  # [CPOL|CPHA] -> polarity 1, phase 0
    # default value
    # spi.lsbfirst = False  # set to MSB_FIRST / most significant bit first
    spi.max_speed_hz = 64000000
    logger.info("init_lcd: DC_PIN=%s, rst=%s",
                RPI.ILI9486.DC_PIN, RPI.ILI9486.RST_PIN)
    global lcd
    lcd = LCD.ILI9486(dc=RPI.ILI9486.DC_PIN,
                      rst=RPI.ILI9486.RST_PIN, spi=spi).begin()
    return lcd


def console_close():
    if lcd is not None:
        lcd.idle()
        lcd.clear().display()
        lcd.begin()
        lcd.sleep()
        # lcd.wake_up()


def console_output(console_output_all_lines: bool = False):
    """Init LCD console and start piping 'journalctl -f' to LCD.

    :console_output_all_lines: console output only on time tick change,
    default False

    :return: Never = does not return

    """
    logger.warning("CONSOLE mode starting - outputting %s log lines to console",
                   "all" if console_output_all_lines else "one/time  tick"
                   )
    lcd = init_lcd()
    proc = subprocess.Popen(["journalctl", "-f"], stdout=subprocess.PIPE)
    stream = io.TextIOWrapper(proc.stdout, encoding="utf-8")
    pipe_stream_to_lcd_console(
        lcd=lcd, stream=stream,
        console_output_all_lines=console_output_all_lines)


def pipe_stream_to_lcd_console(
        lcd: LCD, stream,
        console_output_all_lines: bool,
        max_lines: int | None = None, font_size: int = 15):
    """Read 'stream' and output to 'lcd'

    :console_output_all_lines: console output all lines vs. only one
    line per time tick change.

    :return: Never - loop for ever

    """

    # font_size = 10
    line_height = font_size + 4
    line_width = lcd.dimensions()[0]
    width, height = lcd.dimensions()
    line_step = line_height
    if max_lines is None:
        max_lines = lcd.dimensions()[1]/line_height

    # Font
    picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), font_size)

    # Extrac enverthing after hostname
    hostname = platform.node()

    # Find size of text block

    back_ground = "white"
    lines: deque = deque([])
    lcd_buffer = Image.new("RGB", lcd.dimensions(), back_ground)
    draw = ImageDraw.Draw(lcd_buffer)

    time = None
    for line in stream:

        # discard newline
        line = line.rstrip()

        # try to remove mon and day from start of string
        # : May 16 09:57:25 jrr5 jrr.sh[1803]: 2025-05-16:09:57:25,792 INFO [gpio_coro.py:142] init_GPIO_shutdown: button='26'

        #             Month               day          time              host    rest
        pattern = r'^[A-Za-zåäöÅÄÖ]{3}\s+[0-9]{1,2}\s+(?P<time>[0-9:]+)\s+\w+\s+(?P<rest>.*)'
        match = re.search(pattern, line)
        if match:
            # discard month, day, host
            line = f"{match['time']} {match['rest']}"
            if not console_output_all_lines and time == match["time"]:
                # discard lines on same time -tick
                continue
            else:
                # next time tick started or all lines show - restart time tick
                time = match["time"]

        # Notice if regexp fails just output line from stream
        logger.debug("pipe_stream: inputs line='%s', time='%s'",
                     line, time)
        lines.append(line)

        if len(lines) > max_lines+1:

            lines.popleft()

            # Shift lcd_buffer content up by line_height pixels
            region_to_shift = lcd_buffer.crop((0, line_height, width, height))
            lcd_buffer.paste(region_to_shift, (0, 0))

            # Clear bottom area for new line
            clear_box = (0, height - line_height, width, height)
            draw.rectangle(clear_box, fill=back_ground, outline=None)

            # Draw the new line in empty space at bottom
            draw.text((0, height - line_height), line,
                      font=font, fill=True, anchor='lt')
        else:
            # Draw new line at appropriate y position
            y = (len(lines) - 1) * line_height
            draw.text((0, y), line, font=font, fill=True, anchor='lt')

        # display buffer
        lcd.display(lcd_buffer)


def pipe_stream_orig(lcd: LCD, stream, max_lines: int | None = None, font_size: int = 10):
    """
    Read 'stream' and output to 'lcd'

    :return: Never - loop for ever

    """

    # font_size = 10
    line_height = font_size + 2
    line_width = lcd.dimensions()[0]
    line_step = line_height
    if max_lines is None:
        max_lines = lcd.dimensions()[1]/line_height

    # Font
    picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), font_size)

    # Find size of text block
    lcd_buffer = Image.new("RGB", lcd.dimensions(), "white")
    logger.info(": lcd.dimensions()='%s'", lcd.dimensions())

    lines: deque = deque([])
    for line in stream:
        lines.append(line.rstrip())
        if len(lines) > max_lines:
            lines.popleft()

        logger.debug("pipe_stream: inputs line='%s'", line)

        for i in range(len(lines)):

            text_dimensions = (line_width, line_height)
            line_buffer = Image.new("RGB", text_dimensions, "white")
            line_draw = ImageDraw.Draw(line_buffer)

            text_x = 0
            text_y = 0
            line_draw.text((text_x, text_y), f"{i}:{lines[i]}",
                           font=font, fill=True, anchor='lt')

            # width, height = lcd.dimensions()
            # text_width, text_height = draw.textsize(text, font=font)
            # text_width, text_height = font.getsize(text)
            lcd.display(line_buffer, y0=i*line_step)
