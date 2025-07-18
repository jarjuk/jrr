# *****************************************************************************
# * | File        :	  epd2in13bc.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.0
# * | Date        :   2019-06-20
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

# Async version of epd2in13bc.py from https://github.com/waveshare/e-Paper.git
#
# Changes:
# - epdconfig.delay_ms(100) --> self.delay_ms
# - async def for functions using await
# - import asyncio
# - display imagered default None
# - import epdconfig_async instread of 'epdconfig'
# - added module exit

import asyncio
import logging
# from . import epdconfig
from . import epdconfig_async as epdconfig
# from .epdconfig_async import epdconfig


# Display resolution
EPD_WIDTH       = 104
EPD_HEIGHT      = 212

logger = logging.getLogger(__name__)

class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    # Hardware reset
    async def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        await self.delay_ms(200) 
        epdconfig.digital_write(self.reset_pin, 0)
        await self.delay_ms(5)
        epdconfig.digital_write(self.reset_pin, 1)
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
        
    async def ReadBusy(self):
        logger.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            await self.delay_ms(100)
        logger.debug("e-Paper busy release")

    async def delay_ms(self, ms: int):
        """Implement edpconfig.delay_msg as asyncio sleep"""
        await asyncio.sleep(ms/1000.)

        

    async def init(self):
        if (epdconfig.module_init() != 0):
            return -1
            
        await self.reset()

        self.send_command(0x06) # BOOSTER_SOFT_START
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x17)
        
        self.send_command(0x04) # POWER_ON
        await self.ReadBusy()
        
        self.send_command(0x00) # PANEL_SETTING
        self.send_data(0x8F)
        
        self.send_command(0x50) # VCOM_AND_DATA_INTERVAL_SETTING
        self.send_data(0xF0)
        
        self.send_command(0x61) # RESOLUTION_SETTING
        self.send_data(self.width & 0xff)
        self.send_data(self.height >> 8)
        self.send_data(self.height & 0xff)
        return 0

    def getbuffer(self, image):
        # logger.debug("bufsiz = ",int(self.width/8) * self.height)
        buf = [0xFF] * (int(self.width/8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        # logger.debug("imwidth = %d, imheight = %d",imwidth,imheight)
        if(imwidth == self.width and imheight == self.height):
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        elif(imwidth == self.height and imheight == self.width):
            logger.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy*self.width) / 8)] &= ~(0x80 >> (y % 8))
        return buf

    def module_exit(self):
        logger.debug("About to call 'module_exit'")
        epdconfig.module_exit()
        logger.debug("Return from call 'module_exit'")
    
    async def display(self, imageblack, imagered=None):
        self.send_command(0x10)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imageblack[i])
        # self.send_command(0x92)

        # jj - black/white simulation here
        if imagered is None:
            imagered = imageblack
            
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imagered[i])
        # self.send_command(0x92)
        
        self.send_command(0x12) # REFRESH
        await self.ReadBusy()
        
    async def Clear(self):
        self.send_command(0x10)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.send_command(0x92) 
        
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.send_command(0x92)
        
        self.send_command(0x12) # REFRESH
        await self.ReadBusy()

    async def sleep(self):
        self.send_command(0x02) # POWER_OFF
        await self.ReadBusy()
        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0xA5) # check code
        
        await self.delay_ms(2000)
        epdconfig.module_exit()
### END OF FILE ###

