# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/micropython-cheap-yellow-display-board-cyd-esp32-2432s028r/
 
from machine import Pin, SPI, SoftSPI, ADC, idle
import os, sys, gc
from time import sleep_ms

from modules.sdcard import SDCard
from modules.simple_db import SimpleDB, simpledb_available
from modules.sys_font import SysFont

# Save this file as ili9341.py https://github.com/rdagger/micropython-ili9341/blob/master/ili9341.py
from modules.ili9341 import Display, color565
# Save this file as xglcd_font.py https://github.com/rdagger/micropython-ili9341/blob/master/xglcd_font.py
from modules.xglcd_font import XglcdFont
# Touch screen interface
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
SD_SPI_ID = 1
SD_MISO_PIN = 19
SD_MOSI_PIN = 23
SD_SCK_PIN = 18
SD_CS_PIN = 5

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
log_file_name = "cyd_test_log.txt"
log_file_path = None
log_file_id = None
# Set up display
display = None
touchscreen = None
sys_font = None

def write_log (log_text) :
    global log_file_id
    if log_file_id is not None :
        print (log_text, file = log_file_id)
    elif display is not None :
        display.fill_rectangle (x=0, y=220, w=320, h=20, color=WHITE)
        if sys_font is not None :
            sys_font.text_sysfont (5, 220, log_text, scale=2, text_color=BLACK)
        else :
            display.draw_text8x8(0, 0, log_text, WHITE, BLACK, 0)
        time.sleep_ms (1000)
    else :
        print (log_text)

def initialize_sdcard (mount_dir = "/sd") :
    global log_file_name
    global log_file_path
    global log_file_id
    try :
        spi = SoftSPI (SD_SPI_ID ,
                        sck = Pin (SD_SCK_PIN) ,
                        mosi = Pin (SD_MOSI_PIN) ,
                        miso = Pin (SD_MISO_PIN))
        sd = SDCard (spi ,
                    cs = Pin (SD_CS_PIN))
        # Mount the SD card
        os.mount(sd, mount_dir)
        # Printing the SD direcory may cause a memory fault
        #print ("list sd directory")
        #print(os.listdir('/sd'))
    except Exception as e :
        print (e)
        return None
    write_log ("SDcard mount: " + mount_dir)  
    try :
        log_file_path = mount_dir + "/" + log_file_name
        print ("initialize_sdcard: Opening:" + log_file_path)
        log_file_id = open (log_file_path, "w")
        write_log ("Log file opened")
    except Exception as e :
        print (e)
    gc.collect ()
    return mount_dir
# end initialize_sdcard

def initialize_display () :
    global sys_font
    write_log ("initialize_display")
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
        write_log ("initialize_display: Failed")
        return None
    try :
        sys_font = SysFont (disp)
    except Exception as e :
        print ("init display SysFont:", e)
        write_log ("initialize_display: sys_font Failed")
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
    write_log ("initialize_touchscreen")
    ts = None
    try :
        touchscreen_spi = SPI(TS_SPI_ID,
                                baudrate = TS_BAUDRATE ,
                                sck = Pin (TS_SCK_PIN) ,
                                mosi = Pin (TS_MOSI_PIN) ,
                                miso = Pin (TS_MISO_PIN))
        ts = Touch (touchscreen_spi,
                    cs = Pin (TS_CS_PIN),
                    int_pin = None , #Pin (TS_INT_PIN),
                    int_handler = None) #touchscreen_press)
    except Exception as e :
        print ("init touch:", e)
        pass
    gc.collect ()
    return ts

def draw_text():
    write_log ("draw_text")
    # Clear display
    display.clear(BLACK)

    # Draw the text on (0, 0) coordinates (x, y, text, font color, font background color, rotation)
    display.draw_text8x8(0, 0, 'ESP32 says hello!', WHITE, BLACK, 0)
    
    # Draw the text on the center of the display
    font_size = 8
    text_msg = 'Centered text'
    x_center = int((display.width-len(text_msg)*font_size)/2)
    y_center = int(((display.height)/2)-(font_size/2))
    display.draw_text8x8(x_center, y_center, text_msg, WHITE, BLACK, 0)
    
    # Draw the text on the right with rotation
    display.draw_text8x8(display.width-font_size, 0, 'Text with rotation', WHITE, BLACK, 90)

def draw_font () :
    write_log ("draw_font")
    # Clear display
    display.clear(WHITE)

    # Loading Unispace font
    write_log ('Loading Unispace font...')
    unispace_font = XglcdFont('modules/Unispace12x24.c', 12, 24)
    
    # Draw the text on (0, 0) coordinates (x, y, text, font,  font color, font background color,
    #                                      landscape=False, rotate_180=False, spacing=1)
    display.draw_text(0, 0, 'ESP32 says hello!', unispace_font, BLACK, WHITE)

    # Draw the text on the center of the display
    font_size_w = unispace_font.width
    font_size_h = unispace_font.height
    text_msg = 'Centered text'
    x_center = int((display.width-len(text_msg)*font_size_w)/2)
    y_center = int(((display.height)/2)-(font_size_h/2))
    display.draw_text(x_center, y_center, text_msg, unispace_font, BLACK, WHITE)
    
    # Draw the text with rotation
    display.draw_text(display.width-font_size_h, display.height-font_size_w, 'Text with rotation',
                      unispace_font, BLACK, WHITE, landscape=True)

#-------------------------------------------------------------------------------
def display_tests() :
    write_log  ("display_tests")
    global display
    if display is None :
        write_log ("display not initialized")
        return
    try:
        draw_text ()
        sleep_ms (5000)
        draw_font ()
        sleep_ms (5000)
    except Exception as e:
        print('Error occured: ', e)
    except KeyboardInterrupt:
        print ('Program Interrupted by the user')        
        #display.cleanup()

def touchscreen_tests() :
    write_log ("touchscreen_tests")
    global display
    global touchscreen
    if display is None :
        write_log ("touchscreen_tests: display not initialized")
        return
    if touchscreen is None :
        write_log ("touchscreen_tests: touch screen not initialized")
        return
    quit = False
    display.clear(WHITE)
    sys_font.text_sysfont (5, 5, "Touch Screen", scale=3, text_color=BLACK)
    sys_font.text_sysfont (5, 210, "   Quit   ", scale=3, text_color=BLACK)
    while not quit :
        touch = touchscreen.get_touch()
        if touch is not None :
            x_pos = DISPLAY_WIDTH - touch [1]
            y_pos = DISPLAY_HEIGHT - touch [0]
            touch_text = f"Touch: x = {x_pos}, y = {y_pos}    "
            write_log (touch_text)
            display.fill_rectangle (5, 50, 310, 20, WHITE)
            sys_font.text_sysfont (5, 50, touch_text, scale=2, text_color=BLACK)
            if y_pos >= 210 :
                write_log ("Touch Screen: Quit")
                break
            sleep_ms (500)
        sleep_ms (10)
    display.fill_rectangle (5, 210, 310, 20, WHITE)
    sys_font.text_sysfont (5, 210, "  Goodby  ", scale=3, text_color=BLACK)
    sleep_ms (1000)

def sdcard_tests() :
    write_log ("sdcard_tests")
    global sd_mount
    if sd_mount is None :
        print ("sdcard_tests: SD card not mounted")
        return

DB_ROWS = {
    "customers" : [
        {"key" : "000500" ,
            "name":"Moe" ,
            "dob":19200101 ,
            "occupation":"Three stooges"} ,
        {"key" : "010000" ,
            "name":"Larry" ,
            "dob":19210202 ,
            "occupation":"Three stooges"} ,
        {"key" : "001000" ,
            "name":"Curly" ,
            "dob":19250303 ,
            "occupation":"Three stooges"}
        ] ,
    "invoices" : [
        {"key" : "10000001" ,
            "customer" : "010000"}
        ] ,
    "invoice_lines" : [
        {"key" : ["10000001", "0001"] ,
            "sku" : "12345678" ,
            "quantity" : 12} ,
        {"key" : ["10000001", "0002"] ,
            "sku" : "11223344" ,
            "quantity" : 144 ,
            "price" : "000100.00"}
        ] ,
    "vendors" : [
        {"key" : "100200" ,
            "name" : "IBM" ,
            "balance" : "001500.00"} ,
        {"key" : "101200" ,
            "name" : "Nvidia" ,
            "balance" : "010000.00"}
        ] ,
    "developers" : [
        {"key" : "200100" ,
            "name" : "Curt" ,
            "dob" : 19560606 ,
            "status":"retired"}
        ]
    }

def sdcard_db_tests () :
    global sd_mount
    global SIMPLEDB_PATH
    if not simpledb_available :
        print ("SimpleDB module is not available")
        return
    if sd_mount is None :
        print ("sdcard_db_tests: SD card not mounted")
        return
    SIMPLEDB_PATH = sd_mount + "/test.db"
    try :
        os.remove (SIMPLEDB_PATH)
        print ("db_tests: Removed:", SIMPLEDB_PATH)
    except Exception :
        pass
    # build sample database
    db = SimpleDB (SIMPLEDB_PATH)
    for _, (table_name, table_entries) in enumerate (DB_ROWS.items ()) :
        #print (table_name, entries)
        for _, row in enumerate (table_entries) :
            db.write_row (table_name, row["key"], row)
    display_table_rows (db, "vendors")
    display_table_rows (db, "customers")
    display_table_rows (db, "invoices")
    display_table_rows (db, "invoice_lines")
    display_table_rows (db, "developers")
    db.close ()

# end sdcard_db_tests #

def display_table_rows (db, table_name) :
    row = db.next_row (table_name)
    print (f"## {table_name}")
    while row is not None :
        #if row["key"] !=
        indent = " #"
        for _, (col_name, col_data) in enumerate (row.items()) :
            print (f"{indent}{col_name:15}: {col_data}")
            indent = "  "
        row = db.next_row (table_name, row["key"])
        #print ("next:",row)
        #sleep_ms (2000)

################################################################################

sd_mount = initialize_sdcard ()     # Call first for log output
print ("SD card mount:", sd_mount)
#sys.exit ()
display = initialize_display ()
touchscreen = initialize_touchscreen ()

display_tests ()
touchscreen_tests ()
sdcard_tests ()
sdcard_db_tests ()

if log_file_id is not None :
    log_file_id.close ()
    print ("\nDisplaying log file:")
    with open (log_file_path, "r") as log_file :
        log_line = log_file.readline ()
        while log_line :
            print (log_line, end='')    # Already has NL
            log_line = log_file.readline ()

if sd_mount is not None :
    print ("Unmounting:", sd_mount)
    os.umount (sd_mount)
