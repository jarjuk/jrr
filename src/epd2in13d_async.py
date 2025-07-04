# *****************************************************************************
# * | File        :	  epd2in13d.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.1
# * | Date        :   2022-08-10
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""
Modified from  Waveshare edp demo from https://github.com/waveshare/e-Paper.git based on 'lib/waveshare_epd/epd2in13d.py'

Instruction in https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT_Manual#Working_With_Raspberry_Pi


"""

import logging
# from . import epdconfig
# from lib.waveshare_epd  import epdconfig
import epdconfig_async as epdconfig
from PIL import Image
import RPi.GPIO as GPIO
import asyncio

# Display resolution
EPD_WIDTH = 104
EPD_HEIGHT = 212

logger = logging.getLogger(__name__)


class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        # self.loop = asyncio.get_event_loop()

    lut_vcomDC = [
        0x00, 0x08, 0x00, 0x00, 0x00, 0x02,
        0x60, 0x28, 0x28, 0x00, 0x00, 0x01,
        0x00, 0x14, 0x00, 0x00, 0x00, 0x01,
        0x00, 0x12, 0x12, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00,
    ]

    lut_ww = [
        0x40, 0x08, 0x00, 0x00, 0x00, 0x02,
        0x90, 0x28, 0x28, 0x00, 0x00, 0x01,
        0x40, 0x14, 0x00, 0x00, 0x00, 0x01,
        0xA0, 0x12, 0x12, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_bw = [
        0x40, 0x17, 0x00, 0x00, 0x00, 0x02,
        0x90, 0x0F, 0x0F, 0x00, 0x00, 0x03,
        0x40, 0x0A, 0x01, 0x00, 0x00, 0x01,
        0xA0, 0x0E, 0x0E, 0x00, 0x00, 0x02,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_wb = [
        0x80, 0x08, 0x00, 0x00, 0x00, 0x02,
        0x90, 0x28, 0x28, 0x00, 0x00, 0x01,
        0x80, 0x14, 0x00, 0x00, 0x00, 0x01,
        0x50, 0x12, 0x12, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_bb = [
        0x80, 0x08, 0x00, 0x00, 0x00, 0x02,
        0x90, 0x28, 0x28, 0x00, 0x00, 0x01,
        0x80, 0x14, 0x00, 0x00, 0x00, 0x01,
        0x50, 0x12, 0x12, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_vcom1 = [
        0x00, 0x19, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00,
    ]

    lut_ww1 = [
        0x00, 0x19, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_bw1 = [
        0x80, 0x19, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_wb1 = [
        0x40, 0x19, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    lut_bb1 = [
        0x00, 0x19, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]

    # Hardware reset
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        # epdconfig.delay_ms(200)
        await self.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, 0)
        # epdconfig.delay_ms(5)
        await self.delay_ms(5)
        epdconfig.digital_write(self.reset_pin, 1)
        # epdconfig.delay_ms(200)
        await self.delay_ms(200)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    # send a lot of data
    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    async def ReadBusy(self):
        logger.debug("e-Paper busy")
        while (epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            self.send_command(0x71)
            # epdconfig.delay_ms(100)
            await asyncio.sleep(0.1)
        logger.debug("e-Paper busy release")

    async def delay_ms(self, ms: int):
        """Implement edpconfig.delay_msg as asyncio sleep"""
        await asyncio.sleep(ms/1000.)

    async def TurnOnDisplay(self):
        self.send_command(0x12)
#       epdconfig.delay_ms(100)
        await self.delay_ms(100)
        await self.ReadBusy()

    async def init(self):
        if (epdconfig.module_init() != 0):
            return -1
        # EPD hardware init start
        self.reset()

        self.send_command(0x01)  # POWER SETTING
        self.send_data(0x03)
        self.send_data(0x00)
        self.send_data(0x2b)
        self.send_data(0x2b)
        self.send_data(0x03)

        self.send_command(0x06)  # boost soft start
        self.send_data(0x17)  # A
        self.send_data(0x17)  # B
        self.send_data(0x17)  # C

        self.send_command(0x04)
        await self.ReadBusy()

        self.send_command(0x00)  # panel setting
        self.send_data(0xbf)  # LUT from OTP,128x296
        self.send_data(0x0d)  # VCOM to 0V fast

        self.send_command(0x30)  # PLL setting
        self.send_data(0x3a)  # 3a 100HZ   29 150Hz 39 200HZ	31 171HZ

        self.send_command(0x61)  # resolution setting
        self.send_data(self.width)
        self.send_data((self.height >> 8) & 0xff)
        self.send_data(self.height & 0xff)

        self.send_command(0x82)  # vcom_DC setting
        self.send_data(0x28)
        return 0

    def SetFullReg(self):
        self.send_command(0x82)
        self.send_data(0x00)
        self.send_command(0X50)
        self.send_data(0x97)

        self.send_command(0x20)  # vcom
        self.send_data2(self.lut_vcomDC)
        self.send_command(0x21)  # ww --
        self.send_data2(self.lut_ww)
        self.send_command(0x22)  # bw r
        self.send_data2(self.lut_bw)
        self.send_command(0x23)  # wb w
        self.send_data2(self.lut_wb)
        self.send_command(0x24)  # bb b
        self.send_data2(self.lut_bb)

    def SetPartReg(self):
        self.send_command(0x82)
        self.send_data(0x03)
        self.send_command(0X50)
        self.send_data(0x47)

        self.send_command(0x20)  # vcom
        self.send_data2(self.lut_vcom1)
        self.send_command(0x21)  # ww --
        self.send_data2(self.lut_ww1)
        self.send_command(0x22)  # bw r
        self.send_data2(self.lut_bw1)
        self.send_command(0x23)  # wb w
        self.send_data2(self.lut_wb1)
        self.send_command(0x24)  # bb b
        self.send_data2(self.lut_bb1)

    def getbuffer(self, image):
        # logger.debug("bufsiz = ",int(self.width/8) * self.height)
        buf = [0xFF] * (int(self.width/8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        # logger.debug("imwidth = %d, imheight = %d",imwidth,imheight)
        if (imwidth == self.width and imheight == self.height):
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)
                            ] &= ~(0x80 >> (x % 8))
        elif (imwidth == self.height and imheight == self.width):
            logger.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy*self.width) / 8)
                            ] &= ~(0x80 >> (y % 8))
        return buf

    async def display(self, image):
        if (Image == None):
            return

        if self.width % 8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        self.send_command(0x10)
        self.send_data2([0x00] * self.height * linewidth)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.send_command(0x13)
        self.send_data2(image)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.SetFullReg()
        await self.TurnOnDisplay()

    async def DisplayPartial(self, image):
        if (Image == None):
            return

        self.send_command(0x91)
        self.send_command(0x90)
        self.send_data(0)
        self.send_data(self.width - 1)

        self.send_data(0)
        self.send_data(0)
        self.send_data(int(self.height / 256))
        self.send_data(self.height % 256 - 1)
        self.send_data(0x28)

        if self.width % 8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        buf = [0x00] * self.height * linewidth

        for i in range(self.height * linewidth):
            buf[i] = ~image[i]

        self.send_command(0x10)
        self.send_data2(image)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.send_command(0x13)
        self.send_data2(buf)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.SetPartReg()
        await self.TurnOnDisplay()

    async def Clear(self):
        if self.width % 8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        self.send_command(0x10)
        self.send_data2([0x00] * self.height * linewidth)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.send_command(0x13)
        self.send_data2([0xFF] * self.height * linewidth)
#       epdconfig.delay_ms(10)
        await self.delay_ms(10)

        self.SetFullReg()
        await self.TurnOnDisplay()

    async def sleep(self):
        self.send_command(0X50)
        self.send_data(0xf7)
        self.send_command(0X02)  # power off
        self.send_command(0X07)  # deep sleep
        self.send_data(0xA5)

        #       epdconfig.delay_ms(2000)
        await self.delay_ms(2000)
        # epdconfig.module_exit()
        self.module_exit()
        logger.debug("Return from call 'module_exit'")

    def module_exit(self):
        logger.debug("About to call 'module_exit'")
        epdconfig.module_exit()
        logger.debug("Return from call 'module_exit'")

### END OF FILE ###
