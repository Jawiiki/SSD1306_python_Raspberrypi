from __future__ import division
import time

import busio
from board import *
from adafruit_bus_device.i2c_device import I2CDevice


# Constants
SSD1306_I2C_ADDRESS = 0x3C    # 011110+SA0+RW - 0x3C or 0x3D
SSD1306_SETCONTRAST = 0x81
SSD1306_DISPLAYALLON_RESUME = 0xA4
SSD1306_DISPLAYALLON = 0xA5
SSD1306_NORMALDISPLAY = 0xA6
SSD1306_INVERTDISPLAY = 0xA7
SSD1306_DISPLAYOFF = 0xAE
SSD1306_DISPLAYON = 0xAF
SSD1306_SETDISPLAYOFFSET = 0xD3
SSD1306_SETCOMPINS = 0xDA
SSD1306_SETVCOMDETECT = 0xDB
SSD1306_SETDISPLAYCLOCKDIV = 0xD5
SSD1306_SETPRECHARGE = 0xD9
SSD1306_SETMULTIPLEX = 0xA8
SSD1306_SETLOWCOLUMN = 0x00
SSD1306_SETHIGHCOLUMN = 0x10
SSD1306_SETSTARTLINE = 0x40
SSD1306_MEMORYMODE = 0x20
SSD1306_COLUMNADDR = 0x21
SSD1306_PAGEADDR = 0x22
SSD1306_COMSCANINC = 0xC0
SSD1306_COMSCANDEC = 0xC8
SSD1306_SEGREMAP = 0xA0
SSD1306_CHARGEPUMP = 0x8D
SSD1306_EXTERNALVCC = 0x1
SSD1306_SWITCHCAPVCC = 0x2

# Scrolling constants
SSD1306_ACTIVATE_SCROLL = 0x2F
SSD1306_DEACTIVATE_SCROLL = 0x2E
SSD1306_SET_VERTICAL_SCROLL_AREA = 0xA3
SSD1306_RIGHT_HORIZONTAL_SCROLL = 0x26
SSD1306_LEFT_HORIZONTAL_SCROLL = 0x27
SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = 0x29
SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL = 0x2A

class SSD1306Base(object):
    def __init__(self,i2c_address=SSD1306_I2C_ADDRESS,width=128,height=32):
        self.width = width
        self.height = height
        self._pages = height//8
        self._buffer = bytearray([0]*(width*self._pages))
        self._i2c = I2CDevice(busio.I2C(SCL, SDA), i2c_address)
        
    def _initialize(self):
        raise NotImplementedError
        
        
    def command(self, c):
        temp = bytearray(2)
        temp[0] = 0x00   # Co = 0, DC = 0
        temp[1] = c
        self._i2c.write(temp)
            
            
    def writeList(self,control,star):
        temps = self._buffer[star:star+128].copy()
        temps.insert(0,control)
        self._i2c.write(temps)
    
    def begin(self, vccstate=SSD1306_SWITCHCAPVCC):
        self._vccstate = vccstate
        self._initialize()
        self.command(SSD1306_DISPLAYON)
        
        
    def display(self):
        pg=0
        for i in range(0, len(self._buffer), 128):
            self.command(0xB0 + pg)           # SSD1306_COLUMNADDR
            self.command(0x00)           # Column start address. (0 = reset)
            self.command(0x10)           # Column end address.
            control = 0x40   # Co = 0, DC = 0
            self.writeList(control, i)
            pg = pg + 1
                
                
    def image(self, image):
        if image.mode != '1':
            raise ValueError('Image must be in mode 1.')
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
                .format(self.width, self.height))
        pix = image.load()
        index = 0
        for page in range(self._pages):
            # Iterate through all x axis columns.
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                bits = 0
                # Don't use range here as it's a bit slow
                for bit in [0, 1, 2, 3, 4, 5, 6, 7]:
                    bits = bits << 1
                    bits |= 0 if pix[(x, page*8+7-bit)] == 0 else 1
                # Update buffer byte and increment to next byte.
                self._buffer[index] = bits
                index += 1
                
                
    def clear(self):
        """Clear contents of image buffer."""
        self._buffer = bytearray([0x0f]*(self.width*self._pages))
        
    def set_contrast(self, contrast):
        """Sets the contrast of the display.  Contrast should be a value between
        0 and 255."""
        if contrast < 0 or contrast > 255:
            raise ValueError('Contrast must be a value from 0 to 255 (inclusive).')
        self.command(SSD1306_SETCONTRAST)
        self.command(contrast)
        
        
        
    def dim(self, dim):
        """Adjusts contrast to dim the display if dim is True, otherwise sets the
        contrast to normal brightness if dim is False.
        """
        # Assume dim display.
        contrast = 0
        # Adjust contrast based on VCC if not dimming.
        if not dim:
            if self._vccstate == SSD1306_EXTERNALVCC:
                contrast = 0x9F
            else:
                contrast = 0xCF
            self.set_contrast(contrast)
            
            
            
class SSD1306_128_32(SSD1306Base):
    def __init__(self):
        # Call base class constructor.rst=rst
        super(SSD1306_128_32, self).__init__()
    
    
    
    def _initialize(self):
        # 128x32 pixel specific initialization.
        self.command(SSD1306_DISPLAYOFF)                    # 0xAE
        self.command(SSD1306_SETDISPLAYCLOCKDIV)            # 0xD5 set osc division
        self.command(0xB1)                                  # the suggested ratio 0x80
        self.command(SSD1306_SETMULTIPLEX)                  # 0xA8
        self.command(0x1F)
        self.command(SSD1306_SETDISPLAYOFFSET)              # 0xD3
        self.command(0x10)
        self.command(SSD1306_SETSTARTLINE | 0x0)            # line   SSD1306_SETSTARTLINE  = 0x40
        self.command(SSD1306_SEGREMAP | 0x1)                # SSD1306_SEGREMAP = 0xA0
        self.command(SSD1306_COMSCANDEC)                    # SSD1306_COMSCANDEC = 0xC8
        self.command(0x82)
        self.command(0x00)
        self.command(SSD1306_SETCONTRAST)                   # 0x81
        self.command(0x4D)
        self.command(SSD1306_SETPRECHARGE)                  # 0xd9
        self.command(0x62) 
        self.command(SSD1306_SETVCOMDETECT)                 # 0xDB
        self.command(0x3F)
        self.command(SSD1306_DISPLAYALLON_RESUME)           # 0xA4
        self.command(SSD1306_NORMALDISPLAY)                 # 0xA6
        #self.command(0x32)                                 # PUMP Voltage default value =0x32 SSD1306_CHARGEPUMP = 0x8D		
        self.command(0xAD)                                  # PUMP On/Off
        self.command(0x8B)
        self.command(0xAF)
		
        #self.command(0x00)
        #self.command(0x10)                                 # no offset		
        #self.command(0xB0)									# set page address
        


