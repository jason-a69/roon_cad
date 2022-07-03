import time

from roonapi import RoonApi, RoonDiscovery
from urllib.request import urlopen
from PIL import Image

appinfo = {
    "extension_id": "roon_cad",
    "display_name": "Python program to display cover art on a display",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}

try:
    core_id = open("/etc/roon_cad/my_core_id_file").read()
    token = open("/etc/roon_cad/my_token_file").read()
except OSError:
    print("Please authorise first using discovery.py")
    exit()

"""display_type can be sense for a sense hat,
                       ws1in5 for a waveshare 1.5" SKU14747 """
display_type = "sense"

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

discover = RoonDiscovery(core_id)
server = discover.first()
discover.stop()

roonapi = RoonApi(appinfo, token, server[0], server[1], True)

prev_title = ""
prev_artist = ""
prev_album = ""

while True:
    try:
        zones = []

        zones = roonapi.zones

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
                                display_image = image_roon.resize((basewidth, hsize), Image.ANTIALIAS)

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

            time.sleep(4)

    except KeyboardInterrupt:
        disp.clear()
        break