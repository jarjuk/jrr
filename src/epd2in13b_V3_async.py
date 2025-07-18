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

# Async version of epd2in13b_V3.py from https://github.com/waveshare/e-Paper.git
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
import .epdconfig_async as epdconfig

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
        # epdconfig.delay_ms(200)
        await self.delay_ms(200) 
        epdconfig.digital_write(self.reset_pin, 0)
        # epdconfig.delay_ms(2)
        await self.delay_ms(2)
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
        
    async def ReadBusy(self):
        logger.debug("e-Paper busy")
        self.send_command(0x71);
        while(epdconfig.digital_read(self.busy_pin) == 0): 
            self.send_command(0x71);
            # epdconfig.delay_ms(100)
            await self.delay_ms(100)
        logger.debug("e-Paper busy release")

    async def delay_ms(self, ms: int):
        """Implement edpconfig.delay_msg as asyncio sleep"""
        await asyncio.sleep(ms/1000.)


    async def init(self):
        if (epdconfig.module_init() != 0):
            return -1
            
        await self.reset()
        self.send_command(0x04);  
        await self.ReadBusy();#waiting for the electronic paper IC to release the idle signal

        self.send_command(0x00);    #panel setting
        self.send_data(0x0f);   #LUT from OTP,128x296
        self.send_data(0x89);    #Temperature sensor, boost and other related timing settings

        self.send_command(0x61);    #resolution setting
        self.send_data (0x68);  
        self.send_data (0x00);  
        self.send_data (0xD4);

        self.send_command(0X50);    #VCOM AND DATA INTERVAL SETTING
        self.send_data(0x77);   #WBmode:VBDF 17|D7 VBDW 97 VBDB 57
                            # WBRmode:VBDF F7 VBDW 77 VBDB 37  VBDR B7
        
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
        logger.debug("display: send_command(0x10)")
        self.send_command(0x10)
        logger.debug("loop send_data for imageblack")
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imageblack[i])

        # B&W simulatiohn - use imageblack for imagered
        if imagered is None:
            logger.debug("use imagered = imageblack")
            imagered = imageblack
            
        logger.debug("display: send_command(0x13)")
        self.send_command(0x13)
        logger.debug("loop send_data for imagered")
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imagered[i])

        logger.debug("display: send_command(0x12)")            
        self.send_command(0x12) # REFRESH
        # epdconfig.delay_ms(100)
        logger.debug("display: delay(100)")            
        await self.delay_ms(100)
        logger.debug("display: readBusy")            
        await self.ReadBusy()
        
    async def Clear(self):
        self.send_command(0x10)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        
        self.send_command(0x12) # REFRESH
        # epdconfig.delay_ms(100)
        await self.delay_ms(100)
        await self.ReadBusy()

    async def sleep(self):
        self.send_command(0X50) 
        self.send_data(0xf7)
        self.send_command(0X02) 
        await self.ReadBusy()
        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0xA5) # check code
        
        # epdconfig.delay_ms(2000)
        await self.delay_ms(2000)
        epdconfig.module_exit()
### END OF FILE ###

