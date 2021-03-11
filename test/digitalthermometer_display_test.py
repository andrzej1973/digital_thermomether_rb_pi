#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

#Below line is required to use *C sign
# -*- coding: utf-8 -*-
 
import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
 
# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
 
# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000
 
# Setup SPI bus using hardware SPI:
spi = board.SPI()
 
# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)
 
def BacklightToggle (bcklight): 
    # Turn on/off the backlight
    if bcklight.value == True:
        print("Backlight is Off!")
        bcklight.value = False
    else:
        print("Backlight is On!")
        bcklight.value = True

def DisplayMeasurements(display,image_rotation,font_color,bg_color,intemperaturevalstr,inpressurevalstr,inhumidityvalstr,outtemperaturevalstr):
    # Create blank image for drawing.
    # Make sure to create image with mode 'RGB' for full color.
    height = display.width  # we swap height/width to rotate it to landscape!
    width = display.height
    image = Image.new("RGB", (width, height))
    #rotation = 0
 
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Alternatively load a TTF font.  Make sure the .ttf font file is in the
    # same directory as the python script!
    # Some other nice fonts to try: http://www.dafont.com/bitmap.php
    fontTQtyValue = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 104)
    fontTQtyDeco = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    fontTQtyDecoSmall = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    fontOtherInfo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

    # Draw a black filled box to clear the image.
    #draw.rectangle((0, 0, width, height), outline=0, fill=(26, 163, 255))
    draw.rectangle((0, 0, width, height), outline=0, fill=bg_color)
    
    ###############################
    #Print indoor temperature value
    ###############################
    
    #Print Temperature Indicator, possible value: "T="
    if abs(int(intemperaturevalstr)) < 10:
        #temperature value is single digit
        tqtystr_pos_x=50
    else:
        tqtystr_pos_x=10
        
    indoort_str_pos_base_y = 25
        
    tqtystr_pos_y = indoort_str_pos_base_y
    tqtystr="T"
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDeco, fill=font_color)
    tqtystr_pos_x = tqtystr_pos_x + fontTQtyDeco.getsize(tqtystr)[0] - 5
    tqtystr_pos_y = tqtystr_pos_y + fontTQtyDeco.getsize(tqtystr)[1] - 18
    tqtystr="in"
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDecoSmall, fill=font_color)
    tqtystr_pos_y = indoort_str_pos_base_y
    tqtystr_pos_x = tqtystr_pos_x + fontTQtyDecoSmall.getsize(tqtystr)[0]
    tqtystr="="
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDeco, fill=font_color)

    #Print Temperature Value, possible value: "+/- xxx"
    tvalstr_pos_x= tqtystr_pos_x -12
    tvalstr_pos_y= tqtystr_pos_y -10
    
    if int(intemperaturevalstr) == abs(int(intemperaturevalstr)):
        #temperature value is positive, need to insert space in front of digit...
        intemperaturevalstr = " " + intemperaturevalstr
        
    draw.text((tvalstr_pos_x, tvalstr_pos_y), intemperaturevalstr, font=fontTQtyValue, fill=font_color)

    #Print Temperature Unit, possible value: "*C"
    tunitstr_pos_x = tvalstr_pos_x + fontTQtyValue.getsize(intemperaturevalstr)[0] - 5
    tunitstr_pos_y = tqtystr_pos_y
    tunitstr=chr(176)+"C"
    draw.text((tunitstr_pos_x, tunitstr_pos_y), tunitstr, font=fontTQtyDeco, fill=font_color)
    
    ################################
    #Print outdoor temperature value
    ################################
    
    outdoort_str_pos_base_x = 30
    outdoort_str_pos_base_y = 130
    
    outtstr=""
    if int(outtemperaturevalstr) == abs(int(outtemperaturevalstr)):
        #temperature value is positive - add extra white space
        outtstr = " " + outtstr
    if abs(int(outtemperaturevalstr)) < 10:
        #temperature value is single digit - add extra white space
        outtstr = " " + outtstr
    
    outtstr = outtstr + "[T"
    draw.text((outdoort_str_pos_base_x, outdoort_str_pos_base_y), outtstr, font=fontTQtyDeco, fill=font_color)
    
    outdoortstr_pos_x = outdoort_str_pos_base_x + fontTQtyDeco.getsize(outtstr)[0] - 5
    outdoortstr_pos_y = outdoort_str_pos_base_y + fontTQtyDeco.getsize(outtstr)[1] - 22
    outtstr = "out"
    draw.text((outdoortstr_pos_x, outdoortstr_pos_y), outtstr, font=fontTQtyDecoSmall, fill=font_color)
    outdoortstr_pos_x = outdoortstr_pos_x + fontTQtyDecoSmall.getsize(outtstr)[0]
    outtstr = "=" + outtemperaturevalstr + chr(176) + "C]"
    draw.text((outdoortstr_pos_x, outdoort_str_pos_base_y), outtstr, font=fontTQtyDeco, fill=font_color)    
    
    #Draw division lines
    horizontalline_pos_y = 170
    draw.line((0,horizontalline_pos_y, disp.width,horizontalline_pos_y), fill=font_color)
    draw.line((disp.width/2,horizontalline_pos_y, disp.width/2,disp.height), fill=font_color)


    #Print Pressure reading if available
    pqtystr_pos_x = 5
    pqtystr_pos_y = horizontalline_pos_y + 5
    pqtystr = "P="
    draw.text((pqtystr_pos_x, pqtystr_pos_y), pqtystr, font=fontOtherInfo, fill=font_color)

 
    pvalstr=inpressurevalstr + " hPa"
    
    pvalstr_pos_x = pqtystr_pos_x + 10
    pvalstr_pos_y = pqtystr_pos_y + fontOtherInfo.getsize(pvalstr)[1] + 10
    draw.text((pvalstr_pos_x, pvalstr_pos_y), pvalstr, font=fontOtherInfo, fill=font_color)

    #Print Humidity reading if available
    hqtystr_pos_x = (disp.width/2) + 5
    hqtystr_pos_y = pqtystr_pos_y

    hqtystr = "H="
    draw.text((hqtystr_pos_x, hqtystr_pos_y), hqtystr, font=fontOtherInfo, fill=font_color)

    hvalstr= inhumidityvalstr + " %"

    hvalstr_pos_x = hqtystr_pos_x + 30
    hvalstr_pos_y = hqtystr_pos_y + fontOtherInfo.getsize(hvalstr)[1] + 10
    draw.text((hvalstr_pos_x, hvalstr_pos_y), hvalstr, font=fontOtherInfo, fill=font_color)

    disp.image(image, image_rotation)
    
def ClearDisplay(display,image_rotation):
    height = display.width
    width = display.height
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    disp.image(image, image_rotation)
    
def InitalizeButtons():
    buttonA = digitalio.DigitalInOut(board.D23)
    buttonB = digitalio.DigitalInOut(board.D24)
    buttonA.switch_to_input()
    buttonB.switch_to_input()
    return {"A":buttonA,"B":buttonB}

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()

BacklightToggle (backlight)
DisplayMeasurements(disp,0,"#FFFFFF","#1AA3FF","-10","1030","30","-5")

try:
    button = InitalizeButtons()
    backlight_button=True;
    while (True):
        for i in range(-50,50):
            DisplayMeasurements(disp,0,"#FFFFFF","#1AA3FF",str(i),str(i+1000),str(abs(i)),str(i-25))
            # debounce delay
            time.sleep(.08)
            if button["A"].value == False:
                BacklightToggle (backlight)
except KeyboardInterrupt:
        print("Exiting the program, ctrl+C pressed...")
        ClearDisplay(disp,0)
        BacklightToggle (backlight)