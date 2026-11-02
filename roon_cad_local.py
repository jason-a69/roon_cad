import time
import random
import tomllib

from roonapi import RoonApi, RoonDiscovery
from urllib.request import urlopen
from PIL import Image,ImageFont,ImageDraw,ImageColor
from time import sleep, strftime
from datetime import datetime
from os import path


appinfo = {
    "extension_id": "roon_cad_local",
    "display_name": "Python program to display cover art on a display",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}

with open("/etc/roon/config.toml", "rb") as toml_file:
    config = tomllib.load(toml_file)


core_id = config["server"]["core_id"]
token = config["server"]["token"]
target_zone = config["server"]["target_zone"]

display_type = config["local"]["display_type"]

# Displays supported so far (put these parameters in your [local] header block in /etc/roon/config.toml)
# display_type = "sense"
# https://www.raspberrypi.com/products/sense-hat/
# libraries required to make it work
# sudo apt-get install -y p7zip-full sense-hat
#
# waveshare tiny display
# display_type = "wslin5"
# https://www.waveshare.com/product/ai/displays/oled/1.5inch-rgb-oled-module.htm
#
# 2.0TFT (sourced from Taobao so I cannot share that link here, this is similar)
# display_type = "2.0TFT"
# https://www.alibaba.com/product-detail/2-0-inch-TFT-LCD-LCD_1601295816403.html
# libraries required 
# pip install adafruit-circuitpython-st7789 adafruit-blinka --break-system-packages


if display_type == "sense":
    from sense_hat import SenseHat
    basewidth = 8

    disp = SenseHat()
    # Rotate 180 degrees as the power is going into the top of the Pi Zero
    disp.set_rotation(180)
elif display_type == "ws1in5":
    from waveshare_OLED import OLED_1in5_rgb
    basewidth = 128

    disp = OLED_1in5_rgb.OLED_1in5_rgb()
    disp.Init()

elif display_type == "2.0TFT":
    from xytft import Display

    disp = Display()

    disp.init()


disp.clear()

prev_title = ""
prev_artist = ""
prev_album = ""

def main():
    while True:
        try:
            display_art()
        except KeyboardInterrupt:
            disp.clear()
            break

def display_art():

    zones = []

    zones = roonapi.zones

    prev_title = ""
    prev_artist = ""
    prev_album = ""

    for output in zones.values():
        # Found the zone information we are using"""

        if output["display_name"] == target_zone:

            # If we are playing something then we should display the cover art on our device
            if output["state"] == "playing":
                while True:

                    # Extract the now playing information from the big output tuple"""
                    now_playing = output["now_playing"]
                    title = now_playing["three_line"]["line1"]
                    artist = now_playing["three_line"]["line2"]
                    album = now_playing["three_line"]["line3"]
                    if prev_album.strip() != album.strip():
                        prev_album = album
                        # Get the image key and then use that to get the URL for the art being displayed"""
                        image_key = now_playing.get("image_key")

                        if image_key:
                            image_url = roonapi.get_image(image_key)
                            # Pull the actual picture"""
                            if image_url:

                                # Pull the image from the link
                                image_roon = Image.open(urlopen(image_url))

                                # Shrink the picture to the basewidth (depends on the display)
                                wpercent = (basewidth / float(image_roon.size[0]))
                                hsize = int((float(image_roon.size[1]) * float(wpercent)))
                                display_image = image_roon.resize((basewidth, hsize), Image.ANTIALIAS).convert('RGBA')

                                if display_type == "sense":
                                    # Save the picture and then display it on the sense hat
                                    display_image.save("/tmp/roon.png")
                                    try:
                                        disp.load_image("/tmp/roon.png")
                                    except:
                                        print("Error opening image for album ",album)
                                else:
                                    try:
                                        disp.ShowImage(disp.getbuffer(display_image))
                                    except:
                                        print("Error opening image for album ",album)
                    sleep(1.7)
                    if output["state"] != "playing":

                        # If nothing is playing then clear the display
                        disp.clear()
                        image_roon.close()
                        del image_roon
                        break


main()