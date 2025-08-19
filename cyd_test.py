# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/micropython-cheap-yellow-display-board-cyd-esp32-2432s028r/
 
from machine import Pin, SPI, SoftSPI, ADC, idle
import os
from time import sleep

from modules.sdcard import SDCard

# Save this file as ili9341.py https://github.com/rdagger/micropython-ili9341/blob/master/ili9341.py
from modules.ili9341 import Display, color565
# Save this file as xglcd_font.py https://github.com/rdagger/micropython-ili9341/blob/master/xglcd_font.py
from modules.xglcd_font import XglcdFont
from modules.xpt2046 import Touch


## Display
SPI_ID = 1
BAUDRATE = 60_000_000
SCK_PIN = 14
CS_PIN = 15
DC_PIN = 2
RST_PIN = 15
MOSI_PIN = 13
ROTATION = 90

## Touch screen
TS_SPI_ID = 2
TS_BAUDRATE = 1_000_000
TS_SCK_PIN = 25
TS_MOSI_PIN = 32
TS_MISO_PIN = 39
TS_CS_PIN = 33
TS_INT_PIN = 36

##  RGB LED
RGB_RED_PIN = 4
RGB_GREEN_PIN = 16
RGB_BLUE_PIN = 17

## SD card
SD_MISO_PIN = 19
SD_MOSI_PIN = 23
SD_SCK_PIN = 18
SD_CS_PIN = 5
#SD_DIR = None


#sys.exit()

## LDR
LDR_PIN = 34

## Speaker
SPEAKER_PIN = 26

## Serial communications
SERIAL_TX_PIN = 1
SERIAL_RX_PIN = 3

DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240
WHITE = color565 (255,255,255)
BLACK = color565 (0,0,0)
RED = color565 (255,0,0)
GREEN = color565 (0,255,0)
BLUE = color565 (0,0,255)
BROWN = color565 (165,42,42)
YELLOW_ORANGE = color565 (255,179,67)

# SD card mount
sd_mount = None
# Set up display
display = None
touchscreen = None

def initialize_sdcard (mount_dir = "/sd") :
    try :
        spi = SoftSPI (1,sck=Pin(SD_SCK_PIN),mosi=Pin(SD_MOSI_PIN),miso=Pin(SD_MISO_PIN))
        sd = SDCard (spi,cs=Pin(SD_CS_PIN))
        # Mount the SD card
        os.mount(sd, mount_dir)
        '''
        # Debug print SD card directory and files
        print ("list sd directory")
        print(os.listdir('/sd'))
        # Create / Open a file in write mode.
        # Write mode creates a new file.
        # If  already file exists. Then, it overwrites the file.
        print ("open")
        file = open("/sd/sample3.txt","w")
        file.close ()
        '''
    except Exception as e :
        print (e)
        return None
    gc.collect ()
    return mount_dir
# end initialize_sdcard

def initialize_display () :
    disp = None
    try :
        spi = SPI(SPI_ID,
                    baudrate = BAUDRATE,
                    sck = Pin (SCK_PIN),
                    mosi = Pin (MOSI_PIN))
        disp = Display (spi = spi ,
                        cs = Pin (CS_PIN) ,
                        dc = Pin (DC_PIN) ,
                        rst = Pin (RST_PIN) ,
                        width = DISPLAY_WIDTH ,
                        height = DISPLAY_HEIGHT ,
                        rotation = ROTATION)
        # Turn on display backlight
        backlight = Pin(21, Pin.OUT)
        backlight.on()
    except Exception as e :
        print ("init display:", e)
        pass
    gc.collect ()
    return disp
# end initialize_display #

def touchscreen_press(x, y) :
    #display.clear(black_color)
    print (x,y)
    ## adjust for screen rotation (?)
    x_pos = DISPLAY_WIDTH - y
    y_pos = DISPLAY_HEIGHT - x
    text_touch_coordinates = "Touch: X = " + str(x_pos) + " | Y = " + str(y_pos)
    x_center = int((display.width-len(text_touch_coordinates)*font_size)/2)
    #display.draw_text8x8(x_center, y_center, text_touch_coordinates, WHITE, BLACK, 0)
    print("Touch: X = " + str(x_pos) + " | Y = " + str(y_pos))
    set_op (x_pos, y_pos)

# SPI for touchscreen
def initialize_touchscreen () :
    ts = None
    try :
        touchscreen_spi = SPI(TS_SPI_ID,
                                baudrate=TS_BAUDRATE,
                                sck=Pin(TS_SCK_PIN),
                                mosi=Pin(TS_MOSI_PIN),
                                miso=Pin(TS_MISO_PIN))
        ts = Touch (touchscreen_spi,
                    cs=Pin(TS_CS_PIN),
                    int_pin=Pin(TS_INT_PIN),
                    int_handler=touchscreen_press)
    except Exception as e :
        print ("init touch:", e)
        pass
    gc.collect ()
    return ts

def draw_text():
    # Set colors
    white_color = color565(255, 255, 255)  # white color
    black_color = color565(0, 0, 0)        # black color

    # Turn on display backlight
    #backlight = Pin(21, Pin.OUT)
    #backlight.on()

    # Clear display
    display.clear(black_color)

    # Draw the text on (0, 0) coordinates (x, y, text, font color, font background color, rotation)
    display.draw_text8x8(0, 0, 'ESP32 says hello!', white_color, black_color, 0)
    
    # Draw the text on the center of the display
    font_size = 8
    text_msg = 'Centered text'
    x_center = int((display.width-len(text_msg)*font_size)/2)
    y_center = int(((display.height)/2)-(font_size/2))
    display.draw_text8x8(x_center, y_center, text_msg, white_color, black_color, 0)
    
    # Draw the text on the right with rotation
    display.draw_text8x8(display.width-font_size, 0, 'Text with rotation', white_color, black_color, 90)

#-------------------------------------------------------------------------------
def display_tests() :
    global display
    if display is None :
        print ("display_tests: display not initialized")
        return
    try:
        draw_text()
    except Exception as e:
        print('Error occured: ', e)
    except KeyboardInterrupt:
        print('Program Interrupted by the user')        
        #display.cleanup()

def touchscreen_tests() :
    global display
    global touchscreen
    if display is None :
        print ("touchscreen_tests: display not initialized")
        return
    if touchscreen is None :
        print ("touchscreen_tests: touch screen not initialized")
        return

def sdcard_tests() :
    global sd_mount
    if sd_mount is None :
        print ("sdcard_tests: SD card not mounted")
        return

################################################################################

sd_mount = initialize_sdcard ()
print ("SD card mount:", sd_mount)
display = initialize_display ()
touchscreen = initialize_touchscreen ()

display_tests ()
touchscreen_tests ()
sdcard_tests ()

