"""Wrapping 3.5 inch TFT display wth ili9486 driver.

Wrapper:
- resembles Waveshare ePaper display driver class
- uses async interfaces (even though actually is not async)


"""

import logging
try:
    from .Python_ILI9486 import ILI9486 as LCD
except ImportError:
    from Python_ILI9486 import ILI9486 as LCD

try:
    from spidev import SpiDev
except ModuleNotFoundError:
    pass
from PIL import Image

SCREEN_WIDTH = LCD.LCD_WIDTH
SCREEN_HEIGHT = LCD.LCD_HEIGHT

logger = logging.getLogger(__name__)


# Display resolution


class TFT_DRIVER:
    """Async driver for ILI9486."""

    def __init__(self, dc: int, spi_bus: int, spi_device: int, rst: int = None, ):
        logger.info("Display.init: dc='%s', rst='%s'", dc, rst)
        # GPIO.setmode(GPIO.BCM)
        # self.spi = SpiDev(RPI.ILI9486.SPI_BUS, RPI.ILI9486.SPI_DEVICE)
        self.spi = SpiDev(spi_bus, spi_device)
        self.spi.mode = 0b10  # [CPOL|CPHA] -> polarity 1, phase 0
        # default value
        # spi.lsbfirst = False  # set to MSB_FIRST / most significant bit first
        self.spi.max_speed_hz = 64000000
        self.lcd = LCD.ILI9486(dc=dc, rst=rst, spi=self.spi).begin()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

    async def init(self):
        # self.lcd.idle()
        # self.lcd.clear().display()
        self.lcd.begin()

    async def Clear(self):
        """Clear buffered image = set black color && display it"""
        clear_color = (0, 0, 0)
        self.lcd.clear(color=clear_color).display()

    async def close(self):
        self._close()

    def _close(self):
        self.lcd.idle()
        self.lcd.clear().display()
        self.lcd.begin()
        self.lcd.sleep()

    async def sleep(self):
        self.lcd.sleep()

    async def wake_up(self):
        self.lcd.wake_up()

    async def reset(self):
        self.lcd.sleep()

    async def display(self, image: Image.Image, x0: int = 0, y0: int = 0):
        self._display(image, x0=x0, y0=y0)

    def _display(self, image: Image.Image, x0: int = 0, y0: int = 0):
        logger.debug("_display: image.size='%s', x0=%s, y0=%s",
                     image.size, x0, y0)
        self.lcd.display(image, x0=x0, y0=y0)

    # ----------------------------------------
    # Simulate Waveshare EDP class

    async def display_Fast(self, image: Image.Image, update_base: bool = True):
        self._display(image)

    async def display_Base(self, image: Image.Image):
        self._display(image)

    async def display_Partial(self, image: Image.Image, Xstart: int, Ystart: int, Xend: int, Yend: int):
        logger.debug("display_Partial: image.size='%s', pos (%s,%s,%s,%s)",
                     image.size, Xstart, Ystart, Xend, Yend)
        self._display(image.crop(
            (Xstart, Ystart, Xend, Yend)), x0=Xstart, y0=Ystart)

    def getbuffer(self, image):
        """Remove ALHPA channel - if 'image' has one."""
        if image.mode != "RGB":
            logger.info(
                "getbuffer: image.mode='%s' -> convert to 'RGB'", image.mode)
            image = image.convert("RGB")
        return image

    def module_exit(self):
        self._close()
        logger.debug("About to call 'module_exit'")
