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
#
# Cheap Yellow Display - wheel of fortune demo
#
import time
import random

from machine import SPI, Pin

from modules.ili9341 import Display, color565
from modules.wheel_of_fortune import WheelOfFortune

from modules.xglcd_font import XglcdFont

'''
SPI_ID = 0
BAUDRATE = 100_000_000
SCK_PIN = 2

CS_PIN = 5
DC_PIN = 6
RST_PIN = 7
MOSI_PIN = 3
PHASE = 0
POLARITY = 0
'''
SPI_ID = 1
BAUDRATE = 60_000_000
SCK_PIN = 14
MOSI_PIN = 13
CS_PIN = 15
DC_PIN = 2
RST_PIN = 15
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240
ROTATION = 90
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

WHITE = color565 (255,255,255)
BLACK = color565 (0,0,0)
RED = color565 (255,0,0)
GREEN = color565 (0,255,0)
BLUE = color565 (0,0,255)
BROWN = color565 (165,42,42)
YELLOW_ORANGE = color565 (255,179,67)

DEFAULT_FONT = XglcdFont('modules/Unispace12x24.c', 12, 24)
#DEFAULT_FONT = XglcdFont('modules/IBMPlexMono12x24.c', 12, 24)

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

def solve_it (wof) :
    delay_time = 0.2
    choices_left = []
    for char in "BCDFGHJKLMNPQRSTVWXYZ" :
        choices_left.append (char)
    while len (choices_left) > 0 :
        char = random.choice (choices_left)
        choices_left.remove (char)
        guess_result = "Good"
        guess = wof.guess_character (char)
        if not guess :
            guess_result = "Bad"
        print ("Guessing:", char, guess_result)
        if guess :
            guess_result = "Good "
            delay_time = 1
        else :
            guess_result = "Wrong"
            delay_time = 0.2
        display.draw_text(10, 210, f'Letter: {char} - {guess_result}  ', DEFAULT_FONT, BLACK, WHITE)
        time.sleep (delay_time)

    choices_left = []
    for char in "AEIOU" :
        choices_left.append (char)
    while len (choices_left) > 0 :
        char = random.choice (choices_left)
        choices_left.remove (char)
        guess_result = "Good"
        guess = wof.guess_vowel (char)
        if not guess :
            guess_result = "Bad"
        print ("Guessing (vowels):", char, guess_result)
        if guess :
            guess_result = "Good "
            delay_time = 1
        else :
            guess_result = "Wrong"
            delay_time = 0.2
        display.draw_text(10, 210, f'Vowel: {char} - {guess_result}  ', DEFAULT_FONT, BLACK, WHITE)
        time.sleep (delay_time)

display = initialize_display ()
#
wof = WheelOfFortune (display)
time.sleep (2.0)
#wof.initialize_board ()
wof.initialize_game (bonus_round=False ,
                    category="movie" ,
                    lines=["" ,
                           "butch cassidy" ,
                           "and the" ,
                           "sundance kid"])
#display.draw_text(10, 210, 'Guess', DEFAULT_FONT, BLACK, WHITE)
display.fill_rectangle(10, 210, 300, 24, WHITE)
time.sleep (2.0)
solve_it (wof)
print (wof.complete_phrase)
time.sleep (2.0)

wof.initialize_game (bonus_round=False ,
                    category="phrase" ,
                    lines=["now is the" ,
                           "time to come" ,
                           "to the aid of" ,
                           "your country"])
display.fill_rectangle(10, 210, 300, 24, WHITE)
time.sleep (2.0)
solve_it (wof)
print (wof.complete_phrase)

time.sleep (5)
#display.cleanup()

