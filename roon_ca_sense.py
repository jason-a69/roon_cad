import time

from roonapi import RoonApi, RoonDiscovery
from urllib.request import urlopen
from PIL import Image
from sense_hat import SenseHat

appinfo = {
    "extension_id": "roon_ca_sense",
    "display_name": "Python program to display cover art on a sense hat",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}

try:
    core_id = open("/etc/roon/my_core_id_file").read()
    token = open("/etc/roon/my_token_file").read()
except OSError:
    print("Please authorise first using discovery.py")
    exit()

sense = SenseHat()
sense.clear()
"""Rotate 180 degrees as the power is going into the top of the Pi Zero"""
sense.set_rotation(180)

discover = RoonDiscovery(core_id)
server = discover.first()
discover.stop()

roonapi = RoonApi(appinfo, token, server[0], server[1], True)

"""This is the zone I have my pi / sense hat display in"""
target_zone = "Qutest"

prev_title=""
prev_artist=""
prev_album=""

while True:
    try:
        zones = []

        zones = roonapi.zones

        for output in zones.values():
            """Found the zone information we are using"""
            if output["display_name"] == target_zone:

                """If we are playing something then we should display the cover art on the sense hat"""
                if output["state"] == "playing":
                    """Extract the now playing information from the big output tuple"""
                    now_playing = output["now_playing"]
                    title = now_playing["three_line"]["line1"]
                    artist = now_playing["three_line"]["line2"]
                    album = now_playing["three_line"]["line3"]
                    if prev_album!=album:
                        """Get the image key and then use that to get the URL for the art being displayed"""
                        image_key = now_playing.get("image_key")

                        if image_key:
                            image_url = roonapi.get_image(image_key)
                            """Pull the actual picture"""
                            if image_url:
                                """Shrink the picture to 8 x 8 pixels"""
                                image_roon = Image.open(urlopen(image_url))
                                basewidth = 8
                                wpercent = (basewidth / float(image_roon.size[0]))
                                hsize = int((float(image_roon.size[1]) * float(wpercent)))
                                image_sense = image_roon.resize((basewidth, hsize), Image.ANTIALIAS)
                                """Save the picture and then display it on the sense hat"""
                                image_sense.save("/tmp/roon.png")
                                sense.load_image("/tmp/roon.png")
                        prev_album=album
                else:
                    """If nothing is playing then clear the sense hat"""
                    sense.clear()
                    prev_title=""
                    prev_artist=""
                    prev_album=""

            time.sleep (4)

    except KeyboardInterrupt:
        sense.clear()
        break
