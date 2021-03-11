#!/usr/bin/python3

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

#Below line is required to use *C sign
# -*- coding: utf-8 -*-
 
import time
from datetime import datetime
from threading import Thread
import subprocess
import signal
import logging
import getopt
import sys
import digitalio
import board
import os

import smbus2
import bme280

from w1thermsensor import W1ThermSensor

from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

#Set debug to True in order to log all messages!
LOG_ALL = False
#Set log_to_file flag to False in order to print logs on stdout
LOG_TO_FILE = True

def cmd_usage():
  print ('Usage: '+sys.argv[0]+' {[-d | --debug debug]}')
  exit (1)

try:
    options, arguments = getopt.getopt(sys.argv[1:], 'd', ['debug'])
      
except getopt.GetoptError as err:
    print(str(err))
    cmd_usage()
    sys.exit(1)

for opt, arg in options:
    if opt in ('-d', '--debug'):
        debug = True

#configure logger module
#levels: DEBUG,INFO,WARNING,ERROR,CRITICAL
    
#create two log file handlers, one for actual log file and another for stdout
stdout_handler = logging.StreamHandler(sys.stdout)

if LOG_TO_FILE == True:
    #extract file name from filename.extension
    idx=os.path.split(os.path.basename(__file__))[1].find('.')
    file_name_wo_extension=os.path.split(os.path.basename(__file__))[1][:idx]
    log_file = os.path.dirname(os.path.realpath(__file__)) + "/" + file_name_wo_extension + ".log"
    file_handler = logging.FileHandler(filename=log_file)
    #hndls = [file_handler, stdout_handler]
    hndls = [file_handler]
    print ("Program logs are stored in: ", log_file)
    #f=open(log_file,"w+")
    #f.write("Log file location: " + log_file +"\n")
    #f.close()
else:
    hndls = [stdout_handler]
        
if LOG_ALL == True:
    logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s:%(threadName)s:%(filename)s:%(lineno)s:%(levelname)s:%(message)s', handlers=hndls)
else:
    logging.basicConfig(level = logging.INFO,format = '%(asctime)s:%(threadName)s:%(filename)s:%(lineno)s:%(levelname)s:%(message)s', handlers=hndls)


###################################
#i2c BME280 Configuration settings#
###################################
#i2c bus number
i2c_bus_no = 1
#i2c device address
i2c_address = 0x76

try:
    #initiate i2c bus
    i2c_bus = smbus2.SMBus(i2c_bus_no)
except:
    logging.error('I2C: Failed to initiate i2c bus: %s and exiting the program...', sys.exc_info()[1])
    exit(1)

try:
    bme280_calibration_params = bme280.load_calibration_params(i2c_bus, i2c_address)
except:
    logging.error('BME280: Failed to load calibration data: %s and exiting the program...', sys.exc_info()[1])
    exit(1)
    
try:
    #initialize DS18B2 1-wire sensor
    ds18b2 = W1ThermSensor()
except:
    logging.error('DS18B2: Failed to initialize: %s and exiting the program...', sys.exc_info()[1])
    exit(1)

# Take a single reading from BME280 sensor and return a
# compensated_reading object
try:
    bme280_data = bme280.sample(i2c_bus, i2c_address, bme280_calibration_params)
except:
    logging.error('BME280: Failed to read measurement record: %s and exiting the program...', sys.exc_info()[1])
    exit(1)

# Take single reading from DS18B2 sensor
try: 
    temp = ds18b2.get_temperature()
except:
    logging.error('DS18B2: Failed to read measurement record: %s and exiting the program...', sys.exc_info()[1])
    exit(1)

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



def DisplayMeasurements(display,image_rotation,font_color_primary, font_color_secondary,bg_color,intemperaturevalstr,inpressurevalstr,inhumidityvalstr,outtemperaturevalstr):
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
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDeco, fill=font_color_primary)
    tqtystr_pos_x = tqtystr_pos_x + fontTQtyDeco.getsize(tqtystr)[0] - 5
    tqtystr_pos_y = tqtystr_pos_y + fontTQtyDeco.getsize(tqtystr)[1] - 18
    tqtystr="in"
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDecoSmall, fill=font_color_primary)
    tqtystr_pos_y = indoort_str_pos_base_y
    tqtystr_pos_x = tqtystr_pos_x + fontTQtyDecoSmall.getsize(tqtystr)[0]
    tqtystr="="
    draw.text((tqtystr_pos_x, tqtystr_pos_y), tqtystr, font=fontTQtyDeco, fill=font_color_primary)

    #Print Temperature Value, possible value: "+/- xxx"
    tvalstr_pos_x= tqtystr_pos_x -12
    tvalstr_pos_y= tqtystr_pos_y -10
    
    if int(intemperaturevalstr) == abs(int(intemperaturevalstr)):
        #temperature value is positive, need to insert space in front of digit...
        intemperaturevalstr = " " + intemperaturevalstr
        
    draw.text((tvalstr_pos_x, tvalstr_pos_y), intemperaturevalstr, font=fontTQtyValue, fill=font_color_primary)

    #Print Temperature Unit, possible value: "*C"
    tunitstr_pos_x = tvalstr_pos_x + fontTQtyValue.getsize(intemperaturevalstr)[0] - 5
    tunitstr_pos_y = tqtystr_pos_y
    tunitstr=chr(176)+"C"
    draw.text((tunitstr_pos_x, tunitstr_pos_y), tunitstr, font=fontTQtyDeco, fill=font_color_primary)
    
    
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
    draw.text((outdoort_str_pos_base_x, outdoort_str_pos_base_y), outtstr, font=fontTQtyDeco, fill=font_color_primary)
    
    outdoortstr_pos_x = outdoort_str_pos_base_x + fontTQtyDeco.getsize(outtstr)[0] - 5
    outdoortstr_pos_y = outdoort_str_pos_base_y + fontTQtyDeco.getsize(outtstr)[1] - 22
    outtstr = "out"
    draw.text((outdoortstr_pos_x, outdoortstr_pos_y), outtstr, font=fontTQtyDecoSmall, fill=font_color_primary)
    outdoortstr_pos_x = outdoortstr_pos_x + fontTQtyDecoSmall.getsize(outtstr)[0]
    unitstr = chr(176) + "C]"
    outtstr = "=" + outtemperaturevalstr + unitstr
    draw.text((outdoortstr_pos_x, outdoort_str_pos_base_y), outtstr, font=fontTQtyDeco, fill=font_color_primary)
    
    ticker_pos_x = outdoortstr_pos_x + fontTQtyDeco.getsize(outtstr)[0] + 5
    ticker_pos_y = outdoortstr_pos_y + 5
    tickerstr=chr(187)+chr(171)
    draw.text((ticker_pos_x, ticker_pos_y), tickerstr, font=fontTQtyDecoSmall, fill=font_color_secondary)
    
    #Draw division lines
    horizontalline_pos_y = 170
    draw.line((0,horizontalline_pos_y, disp.width,horizontalline_pos_y), fill=font_color_primary)
    draw.line((disp.width/2,horizontalline_pos_y, disp.width/2,disp.height), fill=font_color_primary)


    #Print Pressure reading if available
    pqtystr_pos_x = 5
    pqtystr_pos_y = horizontalline_pos_y + 5
    pqtystr = "P="
    draw.text((pqtystr_pos_x, pqtystr_pos_y), pqtystr, font=fontOtherInfo, fill=font_color_primary)

 
    pvalstr=inpressurevalstr + " hPa"
    
    pvalstr_pos_x = pqtystr_pos_x + 10
    pvalstr_pos_y = pqtystr_pos_y + fontOtherInfo.getsize(pvalstr)[1] + 10
    draw.text((pvalstr_pos_x, pvalstr_pos_y), pvalstr, font=fontOtherInfo, fill=font_color_primary)

    #Print Humidity reading if available
    hqtystr_pos_x = (disp.width/2) + 5
    hqtystr_pos_y = pqtystr_pos_y

    hqtystr = "H="
    draw.text((hqtystr_pos_x, hqtystr_pos_y), hqtystr, font=fontOtherInfo, fill=font_color_primary)

    hvalstr= inhumidityvalstr + " %"

    hvalstr_pos_x = hqtystr_pos_x + 30
    hvalstr_pos_y = hqtystr_pos_y + fontOtherInfo.getsize(hvalstr)[1] + 10
    draw.text((hvalstr_pos_x, hvalstr_pos_y), hvalstr, font=fontOtherInfo, fill=font_color_primary)

    disp.image(image, image_rotation)
    
def ClearDisplay(display,image_rotation):
    height = display.width
    width = display.height
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    disp.image(image, image_rotation)
    
def InitalizeButtons():
    #Button B (upper) - will be used to turn display on and off
    #Button A (bottom) - will be used to Reboot or Halt RB
    buttonA = digitalio.DigitalInOut(board.D23)
    buttonB = digitalio.DigitalInOut(board.D24)
    buttonA.switch_to_input()
    buttonB.switch_to_input()
    return {"A":buttonA,"B":buttonB}

 
def BacklightToggle (bcklight): 
    # Turn on/off the backlight
    if bcklight.value == True:
        logging.info('Backlight is Off!')
        bcklight.value = False
    else:
        logging.info('Backlight is On!')
        bcklight.value = True
        
def PiRestart():
    logging.info('Restart Button Pressed, restarting Pi...!')
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    logging.info(output)

# modular function to shutdown Pi
def PiShutDown():
    logging.info('Restart Button Pressed for 3 sec., shutting down Pi...!')
    
    #Turn off Pi's display so kernel panic, which is triggered after default 3sec
    #is not visible
    #command = "/usr/bin/sudo /usr/bin/tvservice -o"
    #command = "/usr/bin/sudo /usr/bin/vcgencmd display_power 0"
    #process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    #output = process.communicate()[0]
    #logging.info(output)
    
    #time.sleep (10)
    
    #Shut down Pi safely
    command = "/usr/bin/sudo /sbin/shutdown -h now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    logging.info(output)

    
# Define a function for button handling thread
def ButtonHandlingThread(bclt,button):
    global thread_exit
    backlight_button=True
    reset_button_pressed=False
    reset_counter = 0
    logging.info('Starting Button Handling Thread!')
    while (True):
        
        if thread_exit == True:
            break
        time.sleep(.1) # this sleep is to help ignoring button rebouncing 
        
        if button["B"].value == False and backlight_button == True:
            BacklightToggle (bclt)
            backlight_button = False
        elif button["B"].value == True:
            backlight_button = True        
        if button["A"].value == False: #reset button pressed
            reset_counter = reset_counter + 1
            reset_button_pressed=True
        else: #reset button not pressed
            if reset_button_pressed == True and reset_counter > 30: # reset button has just been released after long press
                logging.info('Restart button long press!')
                reset_button_pressed=False
                PiShutDown()
            elif reset_button_pressed == True: # reset button has just been released after short press
                logging.info('Restart button short press!')
                reset_button_pressed=False
                PiRestart()
            reset_counter = 0   
                
        
      
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()

buttons = InitalizeButtons()

BacklightToggle (backlight)

thread_exit = False
thread = Thread(target = ButtonHandlingThread, name = "ButtonHndlThread", args = (backlight, buttons, ))
thread.start()

def handleSIGTERM(signum, frame):
    global backlight
    global thread_exit
    global disp
    logging.info('Exiting the program, SIGTERM received...')
    ClearDisplay(disp,0)
    backlight.value = False
    thread_exit = True
    thread.join()
    exit(0)


#turn off backlight and clean screen when SIGTERM is received i.e.:
# at service stop
# when kill command is send to the process/service
# when system is rebooted
signal.signal(signal.SIGTERM, handleSIGTERM)

secondary_color = "#FFFFFF"

while (True):
    try:
        bme280_data = bme280.sample(i2c_bus, i2c_address, bme280_calibration_params)
        
        logging.debug('Measurement sample from BME280 sensor:')
        logging.debug('   id: %s',str(bme280_data.id))
        logging.debug('   timestamp: %s',str(bme280_data.timestamp))
        logging.debug('   temperature: %f',float(bme280_data.temperature))
        logging.debug('   pressure: %f',float(bme280_data.pressure))
        logging.debug('   humidity: %f', float(bme280_data.humidity))
        
        ds18b2_data = ds18b2.get_temperature()
        ds18b2_data=str(round(float(ds18b2_data)))
        now = datetime.now() # current date and time
        timestamp_str=now.strftime("%Y:%m:%d %H:%M:%S.%f")
        
        logging.debug('Measurement sample from DS18B2 sensor:')
        logging.debug('   id: %s',ds18b2.id)
        logging.debug('   timestamp: %s',timestamp_str)
        logging.debug('   temperature: %s C',ds18b2_data)
        
        if secondary_color == "#FFFFFF":
            secondary_color = "#1AA3FF"
        else:
            secondary_color = "#FFFFFF"
            
        DisplayMeasurements(disp,0,"#FFFFFF", secondary_color,"#1AA3FF",str(round(bme280_data.temperature)),str(round(bme280_data.pressure)),str(round(bme280_data.humidity)),ds18b2_data)
            
    except KeyboardInterrupt:
        logging.info('Exiting the program, ctrl+C pressed...')
        ClearDisplay(disp,0)
        backlight.value=False
        #set exit flag for the thread and wait for it to finish
        thread_exit = True
        thread.join()
        exit(0)
    except Exception as e:
        logging.warning('Other exception cought, just ignore it and proceed!')
        logging.warning(e)
        pass
    
    #Observe SIGTERM signal is handled in code above!

thread_exit = True
thread.join()
