
#!/bin/python
#This script was authored by AndrewH7 and belongs to him (www.instructables.com/member/AndrewH7)
#You have permission to modify and use this script only for your own personal usage
#You do not have permission to redistribute this script as your own work
#Use this script at your own risk

import RPi.GPIO as GPIO
import serial
import os

gpio_pin_number = 21
#Replace YOUR_CHOSEN_GPIO_NUMBER_HERE with the GPIO pin number you wish to use
#Make sure you know which rapsberry pi revision you are using first
#The line should look something like this e.g. "gpio_pin_number=7"

GPIO.setmode(GPIO.BCM)
#Use BCM pin numbering (i.e. the GPIO number, not pin number)
#WARNING: this will change between Pi versions
#Check yours first and adjust accordingly

GPIO.setup(gpio_pin_number, GPIO.IN, pull_up_down = GPIO.PUD_UP)
#It's very important the pin is an input to avoid short-circuits
#The pull-up resistor means the pin is high by default

try:
    # informo que la raspberry esta encendida
    port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)
    port.write("on")
    port.close()
    #Use falling edge detection to see if pin is pulled
    #low to avoid repeated polling
    GPIO.wait_for_edge(gpio_pin_number, GPIO.FALLING)
    # informo que esta siendo apagada
    port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)
    port.write("off")
    port.close()
    #Revert all GPIO pins to their normal states (i.e. input = safe)
    GPIO.cleanup()

    #Send command to system to shutdown
    os.system("sudo shutdown -h now")
except:
    pass


