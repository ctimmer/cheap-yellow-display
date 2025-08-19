# -*-coding:utf-8 -*-
#
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2025 Curt Timmerman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################


import sys, os, gc
from machine import SPI, Pin, SoftSPI, freq
import time

from modules.sdcard import SDCard
from modules.ili9341 import Display, color565
from modules.xpt2046 import Touch

from modules.sprite_handler import SpriteHandler
from modules.sys_font import SysFont

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

ODOMETER_DIGITS = 6
ODOMETER_MOD = int (10 ** ODOMETER_DIGITS)
ODOMETER_MAX = ODOMETER_MOD - 1
ODOMETER_FORMAT = "{:0" + str (ODOMETER_DIGITS) + "d}"
ODOMETER_X = 20
ODOMETER_Y = 20
ODOMETER_DIGIT_OFFSET = 24
OD_DIGIT_FILE = "images/odomdigits.raw"
OD_SHEET_WIDTH = 170
OD_SHEET_HEIGHT = 20
OD_IMAGE_WIDTH = 17
OD_IMAGE_HEIGHT = 20
OD_PADDING = 2
OD_WIDTH = OD_IMAGE_WIDTH + (OD_PADDING * 2)
OD_HEIGHT = OD_IMAGE_HEIGHT + (OD_PADDING * 2)
OD_BACKGROUND = BLACK

display = None
touchscreen = None
sddir = None

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
    touchscreen_spi = SPI(TS_SPI_ID,
                        baudrate=TS_BAUDRATE,
                        sck=Pin(TS_SCK_PIN),
                        mosi=Pin(TS_MOSI_PIN),
                        miso=Pin(TS_MISO_PIN))
    ts = Touch(touchscreen_spi,
                    cs=Pin(TS_CS_PIN),
                    int_pin=Pin(TS_INT_PIN),
                    int_handler=touchscreen_press)
    gc.collect ()
    return ts

ODOMETER = []
digit_data = {}

SCROLL_HEIGHT = 5
SCROLL_SEPARATION = 2

def scroll_digit_up (digit, scroll, odometer_digit) :
    #print ("gpi:", image_data)
    if scroll not in [1, 2, 3] :
        print (f"Invalid scroll value: {scroll}")
        return None
    next_key = "next"
    image_data = digit_data [digit]
    x_display = odometer_digit ["x_image"]
    y_display = odometer_digit ["y_image"]
    x_sprite = image_data ["x"]
    y_sprite = image_data ["y"] + ((SCROLL_HEIGHT * scroll) + SCROLL_SEPARATION)
    w_image = image_data ["w"]
    h_image = image_data ["h"] - ((SCROLL_HEIGHT * scroll) + SCROLL_SEPARATION)

    display.draw_sprite (odom_images.get_sprite (x_sprite,
                                                 y_sprite,
                                                 w_image,
                                                 h_image) ,
                            x = x_display,                # screen position
                            y = y_display,
                            w = w_image,               # image dimensions
                            h = h_image)
    #
    y_display += h_image
    #print (f"sep: y={y_display}, h={SCROLL_SEPARATION}")
    display.fill_rectangle (x=x_display, y=y_display, w=w_image, h=SCROLL_SEPARATION, color=OD_BACKGROUND)
    y_display += SCROLL_SEPARATION
    image_data = digit_data [image_data[next_key]]
    x_sprite = image_data ["x"]
    y_sprite = image_data ["y"]
    w_image = image_data ["w"]
    h_image = (SCROLL_HEIGHT * scroll) - SCROLL_SEPARATION
    #print (f"new: y={y_display}, h={h}")
    display.draw_sprite (odom_images.get_sprite (x_sprite, y_sprite, w_image, h_image) ,
                            x = x_display,                # screen position
                            y = y_display,
                            w = w_image,               # image dimensions
                            h = h_image)

# endscroll_digit_up #

def scroll_digit_down (digit, scroll, odometer_digit) :
    #print ("gpi:", odometer_digit)
    if scroll not in [1, 2, 3] :
        print (f"Invalid scroll value: {scroll}")
        return None
    '''
    display.fill_rectangle (x=odometer_digit ["x_image"],
                            y=odometer_digit ["y_image"],
                            w=OD_IMAGE_WIDTH,
                            h=OD_IMAGE_HEIGHT,
                            color=OD_BACKGROUND)
    '''
    next_key = "prev"
    image_data = digit_data [digit]
    x_display = odometer_digit ["x_image"]
    y_display = odometer_digit ["y_image"] + ((SCROLL_HEIGHT * scroll) + SCROLL_SEPARATION)
    x_sprite = image_data ["x"]
    y_sprite = image_data ["y"] # + ((SCROLL_HEIGHT * scroll) + SCROLL_SEPARATION)
    w_image = image_data ["w"]
    h_image = image_data ["h"] - ((SCROLL_HEIGHT * scroll) + SCROLL_SEPARATION)
    
    display.draw_sprite (odom_images.get_sprite (x_sprite,
                                                 y_sprite,
                                                 w_image,
                                                 h_image) ,
                            x = x_display,                # screen position
                            y = y_display,
                            w = w_image,               # image dimensions
                            h = h_image)
    
    #
    #return
    y_display -= SCROLL_SEPARATION
    #print (f"sep: y={y_display}, h={SCROLL_SEPARATION}")
    display.fill_rectangle (x=x_display, y=y_display, w=w_image, h=SCROLL_SEPARATION, color=OD_BACKGROUND)
    #return
    y_display = odometer_digit ["y_image"]
    image_data = digit_data [image_data[next_key]]
    x_sprite = image_data ["x"]
    y_sprite = image_data ["y"] + (SCROLL_HEIGHT * (4 - scroll))
    w_image = image_data ["w"]
    h_image = image_data ["h"] - (SCROLL_HEIGHT * (4 - scroll))
    #print (f"new: spr: x={x_sprite} y={y_sprite} img: w={w_image} h={h_image}")
    display.draw_sprite (odom_images.get_sprite (x_sprite, y_sprite, w_image, h_image) ,
                            x = x_display,                # screen position
                            y = y_display,
                            w = w_image,               # image dimensions
                            h = h_image)

# end scroll_digit_down #

def scroll_digit (digit, scroll_level, scroll_up, odometer_digit) :
    #print ("### scroll_digit:", digit, scroll)
    if scroll_level not in [1, 2, 3, 4] :
        print (f"Invalid scroll value: {scroll_level}")
        return None

    #image_data = digit_data [digit]
    if scroll_level >= 4 :
        ## Done  scrolling, display current digit
        next_key = "next"
        if not scroll_up :
            next_key = "prev"
        image_data = digit_data [digit]
        image_data = digit_data [image_data[next_key]]
        display.draw_sprite (odom_images.get_sprite (image_data["x"],
                                                     image_data["y"],
                                                     OD_IMAGE_WIDTH,
                                                     OD_IMAGE_HEIGHT) ,
                            x = odometer_digit ["x_image"],                # screen position
                            y = odometer_digit ["y_image"],
                            w = OD_IMAGE_WIDTH,               # image dimensions
                            h = OD_IMAGE_HEIGHT)
        return
    #
    if scroll_up :
        scroll_digit_up (digit, scroll_level, odometer_digit)
    else :
        scroll_digit_down (digit, scroll_level, odometer_digit)

# end scroll_digit #

odometer_int = 0    # current odometer reading
odometer_str = ""   # string value of odometer_int

def adjust_odometer (increment = 0) :
    global odometer_int
    odometer_int += increment
    if odometer_int > ODOMETER_MAX :
        odometer_int = 0
    elif odometer_int < 0 :
        odometer_int = ODOMETER_MAX

def odometer_increment (increment = 1) :
    global odometer_int
    global odometer_str
    inc_count = increment
    inc_value = 1
    inc_positive = increment >= 0
    if not inc_positive :
        inc_value = -1
        inc_count = abs (increment)
    while inc_count > 0 :
        adjust_odometer (inc_value)
        new_str = ODOMETER_FORMAT.format (odometer_int)
        ## Make a list of all digit indexes that have changed
        change_list = []
        for digit_idx, digit in enumerate (odometer_str) :
            if digit != new_str [digit_idx] :
                change_list.append (digit_idx)  # digit changed
        ## Scroll changed digits
        for scroll_level in range (1,5) :
            for digit_idx in change_list :
                scroll_digit (odometer_str [digit_idx] ,
                                scroll_level ,
                                inc_positive ,
                                ODOMETER [digit_idx])
            time.sleep (0.02)
        odometer_str = new_str
        inc_count -= 1

# end odometer_increment #

def odometer_init (start=0) :
    global ODOMETER
    global odometer_int
    global odometer_str
    odometer_int = start
    adjust_odometer ()
    odometer_str = ODOMETER_FORMAT.format (odometer_int) # f"{odometer_int:04d}"
    odometer_x = ODOMETER_X
    odometer_y = ODOMETER_Y
    for digit_idx in range (0, ODOMETER_DIGITS) :
        digit_pos = {
            "x_field" : odometer_x ,
            "y_field" : ODOMETER_Y ,
            "w_field" : OD_IMAGE_WIDTH + (2 * OD_PADDING) ,
            "h_field" : OD_IMAGE_HEIGHT + (2 * OD_PADDING) ,
            "x_image" : odometer_x + OD_PADDING ,
            "y_image" : ODOMETER_Y + OD_PADDING
            }
        ODOMETER.append (digit_pos)
        display.fill_rectangle (x=digit_pos["x_field"] ,
                                y=digit_pos["y_field"] ,
                                w=digit_pos ["w_field"] ,
                                h=digit_pos ["h_field"] ,
                                color=OD_BACKGROUND)
        #print (digit_pos)
        display.draw_sprite (odom_images [int (odometer_str [digit_idx])],
                                x = digit_pos["x_image"] ,
                                y = digit_pos["y_image"] ,
                                w = OD_IMAGE_WIDTH ,
                                h = OD_IMAGE_HEIGHT)
        odometer_x += ODOMETER_DIGIT_OFFSET
    ## Initialize digit data
    for img_idx in range (0,10) :
        #print (odom_images.get_index_sprite_data (img_idx))
        digit_key = str (img_idx)
        digit_data [digit_key] = odom_images.get_index_sprite_data (img_idx)
        digit_data [digit_key]["next"] = str ((img_idx + 1) % 10)
        down_digit = img_idx - 1
        if down_digit < 0 :
            down_digit = 9
        digit_data [digit_key]["prev"] = str (down_digit)

# end odometer_init #

################################################################################

try :
    freq(240000000)
except :
    pass

sd_dir = initialize_sdcard ()
display = initialize_display ()
touchscreen = initialize_touchscreen ()

sysfont = SysFont (display)

print ("CPU freq:", freq())
print ("SD card mount:", sd_dir)

odom_images = SpriteHandler ()
odom_images.load_raw_file (OD_DIGIT_FILE ,
                            image_width = OD_IMAGE_WIDTH ,
                            image_height = OD_IMAGE_HEIGHT)

display.clear (WHITE)
# display sprite sheet
#display.draw_image(path=OD_DIGIT_FILE, x=10, y=110, w=OD_SHEET_WIDTH, h=OD_SHEET_HEIGHT)
#sys.exit ()

odometer_init ()
for _ in range (1) :
    odometer_increment (10)
time.sleep (2.0)
for _ in range (2) :
    odometer_increment (-10)
#display.cleanup()
#sys.exit ()

'''
sysfont.text_sysfont (10 ,
                            60 ,
                            "Button 1: Increment by 1" ,
                            scale = 2 ,
                            text_color = BLACK)
'''

font_size = 8
y_center = int(((display.height)/2)-(font_size/2))
op = None

TOUCH_BUTTONS = [
    {
    "op" : "u1" ,
    "x" : 10 ,
    "y" : 200 ,
    "w" : 20 ,
    "h" : 20 ,
    "color" : WHITE ,
    "bg" : GREEN
    } ,
    {
    "op" : "d1" ,
    "x" : 40 ,
    "y" : 200 ,
    "w" : 20 ,
    "h" : 20 ,
    "color" : WHITE ,
    "bg" : RED
    } ,
    {
    "op" : "q" ,
    "x" : 290 ,
    "y" : 200 ,
    "w" : 20 ,
    "h" : 20 ,
    "color" : WHITE ,
    "bg" : YELLOW_ORANGE
    }
    ]

for _, button in enumerate (TOUCH_BUTTONS) :
    button ["x_max"] = button ["x"] + button ["w"] - 1
    button ["y_max"] = button ["y"] + button ["h"] - 1
    display.fill_rectangle (x=button["x"] ,
                                y=button["y"] ,
                                w=button ["w"] ,
                                h=button ["h"] ,
                                color = button ["bg"])
    #print (button)

def set_op (x, y) :
    global op
    for _, button in enumerate (TOUCH_BUTTONS) :
        if x >= button["x"] and x <= button["x_max"] \
        and y >= button["y"] and y <= button["y_max"] :
            op = button ["op"]
            #print (op)
            break

wait_time_ms = 100
wait_ms = time.ticks_ms()
try:
    # Run the event loop indefinitely
    while True:
        # Loop to wait for touchscreen press
        if time.ticks_diff (time.ticks_ms(), wait_ms) > 0 :
            if touchscreen.raw_touch() is not None :
                touchscreen.get_touch()
                if op is not None :
                    print (op)
                    if op == "u1" :
                        odometer_increment (1)
                    elif op == "d1" :
                        odometer_increment (-1)
                    elif op == "q" :
                        break
                    op = None
                wait_ms = time.ticks_ms() + wait_time_ms
except Exception as e:
    print('Error occured: ', e)
except KeyboardInterrupt:
    print('Program Interrupted by the user')        
finally:
    sysfont.text_sysfont (10, 160, "That's All Folks", scale=3, text_color=BLACK)
    time.sleep (3)
    display.cleanup()
