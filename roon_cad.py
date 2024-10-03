import time
import random

from roonapi import RoonApi, RoonDiscovery
from urllib.request import urlopen
from PIL import Image,ImageFont,ImageDraw,ImageColor
from time import sleep, strftime
from datetime import datetime
from os import path


appinfo = {
    "extension_id": "roon_cad",
    "display_name": "Python program to display cover art on a display",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}

authorized_yn = "Y"

my_core_id_file = "/etc/roon_cad/my_core_id_file"
if path.exists(my_core_id_file):
    core_id = open(my_core_id_file).read()
else:
    core_id = "None"

my_token_file = "/etc/roon_cad/my_token_file"
if path.exists(my_token_file):
    token = open(my_token_file).read()
else:
    token = "None"

"""display_type can be sense for a sense hat,
                       ws1in5 for a waveshare 1.5" SKU14747 """
display_type = "ws1in5"

"""This is the zone I have my Raspberry Pi in"""
target_zone = "Qutest"

if display_type == "sense":
    basewidth = 8
    from sense_hat import SenseHat

    disp = SenseHat()
    disp.clear()
    """Rotate 180 degrees as the power is going into the top of the Pi Zero"""
    disp.set_rotation(180)
elif display_type == "ws1in5":
    basewidth = 128
    from waveshare_OLED import OLED_1in5_rgb

    disp = OLED_1in5_rgb.OLED_1in5_rgb()
    disp.Init()
    disp.clear()

if token == "None":
    authorized_yn = "N"
else:
    discover = RoonDiscovery(core_id)
    server = discover.first()
    discover.stop()
    roonapi = RoonApi(appinfo, token, server[0], server[1], True)

    with open(my_token_file, "w") as f:
        f.write(str(roonapi.token))


prev_title = ""
prev_artist = ""
prev_album = ""

def main():
    while True:
        try:
            if authorized_yn == "Y":
                display_art()
            else:
                display_time()

        except KeyboardInterrupt:
            disp.clear()
            break

def display_time():
    image1 = Image.new('RGB', (disp.width, disp.height), ImageColor.getrgb("BLACK"))
    draw = ImageDraw.Draw(image1)

    colour = random.randint(0,5)
    if colour == 0:
        colourt = "WHITE"
    elif colour == 1:
        colourt = "BLUE"
    elif colour == 2:
        colourt = "RED"
    elif colour == 3:
        colourt = "GREEN"
    elif colour == 4:
        colourt = "YELLOW"
    else:
        colourt = "CYAN"

    font = ImageFont.truetype('/usr/local/bin/Font.ttc', 50)
    draw.text((random.randint(0,1),random.randint(0,80)),datetime.now().strftime('%H:%M\n'), font = font, fill = (random.randint(0
,255),random.randint(0,255),random.randint(0,255)))
    image1 = image1.rotate(0)
    disp.ShowImage(disp.getbuffer(image1))

def display_art():

    zones = []

    zones = roonapi.zones

    prev_title = ""
    prev_artist = ""
    prev_album = ""

    """ Set up displaying_art variable, if it is set to "Y" then do not display the clock at the end of the loop """
    displaying_art = "N"
    for output in zones.values():
        """Found the zone information we are using"""

        if output["display_name"] == target_zone:

            """If we are playing something then we should display the cover art on our device"""
            if output["state"] == "playing":
                """Extract the now playing information from the big output tuple"""
                now_playing = output["now_playing"]
                title = now_playing["three_line"]["line1"]
                artist = now_playing["three_line"]["line2"]
                album = now_playing["three_line"]["line3"]
                displaying_art = "Y"
                if prev_album != album:
                    """Get the image key and then use that to get the URL for the art being displayed"""
                    image_key = now_playing.get("image_key")

                    if image_key:
                        image_url = roonapi.get_image(image_key)
                        """Pull the actual picture"""
                        if image_url:

                            """Pull the image from the link"""
                            image_roon = Image.open(urlopen(image_url))

                            """Shrink the picture to the basewidth (depends on the display"""
                            wpercent = (basewidth / float(image_roon.size[0]))
                            hsize = int((float(image_roon.size[1]) * float(wpercent)))
                            display_image = image_roon.resize((basewidth, hsize), Image.ANTIALIAS).convert('RGBA')

                            txt = Image.new('RGBA', display_image.size, (255,255,255,0))

                            text = datetime.now().strftime('%H:%M\n')
                            font = ImageFont.truetype('/usr/local/bin/Font.ttc', 12)

                            d = ImageDraw.Draw(txt)
                            width, height = display_image.size

                            textwidth, textheight = d.textsize(text, font)
                            x=width-textwidth
                            y=height-textheight

                            d.text((x,y), text, fill=(255,255,255, 255), font=font)

                            display_image = Image.alpha_composite(display_image, txt)


                            if display_type == "sense":
                                """Save the picture and then display it on the sense hat"""
                                display_image.save("/tmp/roon.png")
                                try:
                                    disp.load_image("/tmp/roon.png")
                                except:
                                    print("Error opening image for album ",album)
                            elif display_type == "ws1in5":
                                """On the waveshare it is much easier to display"""
                                try:
                                    disp.ShowImage(disp.getbuffer(display_image))
                                except:
                                    print("Error opening image for album ",album)
                    prev_album = album
            else:
                """If nothing is playing then clear the display"""
                disp.clear()
                prev_title = ""
                prev_artist = ""
                prev_album = ""

                display_time()
                sleep(60)

    if displaying_art == "N":
        disp.clear()
        display_time()
        sleep(60)

main()