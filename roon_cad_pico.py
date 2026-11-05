# This code is used to send a cover art picture to a Raspberry Pico2 W
# connected on the same network as the roon server.
#
# Before you can use this, you need to run discovery.py which will populate your
# roon server parameters. 
# The server parameters are stored in
#
# /etc/roon/config.toml
#
# The file will look something like this after discovery.py has been run
#
#[server]
# host = "<ip address>"
# core_name = "roon"
# core_id = "<big string>"
# token = "<big_string>"
#
# You also need to have a target zone line under the server parameters block, this is 
# required so that the art is displayed for that zone
#
# target_zone = "Qutest"
#
# The Pico parameters are stored in the same file underneath the server parameters
# For example
#
# [pico]
# ip = "<ip address>"
# port = 5000
# basewidth = 48
#
# ip is the address where the Pico is connected 
# port is the receiving port. Leave this at 5000
# basewidth will depend on your RGB matrix. In my case I have a 96x48 display
# so I am displaying the cover art on the right hand side, the left is reserved
# for a clock
#

import socket
import time
import io
import struct
import gc
import tomllib

from roonapi import RoonApi, RoonDiscovery
from urllib.request import urlopen
from PIL import Image,ImageFont,ImageDraw,ImageColor
from os import path
from time import sleep

appinfo = {
    "extension_id": "roon_cad_pico",
    "display_name": "Python program to display cover art on a Pi Pico display",
    "display_version": "1.0.0",
    "publisher": "jason-a69",
    "email": "email@yahoo.co.uk",
}


with open("/etc/roon/config.toml", "rb") as toml_file:
    config = tomllib.load(toml_file)

pico_ip = config["pico"]["ip"]
port = config["pico"]["port"]
basewidth = config["pico"]["basewidth"]

target_size = (int(basewidth),int(basewidth))
core_id = config["server"]["core_id"]
token = config["server"]["token"]
target_zone = config["server"]["target_zone"]

discover = RoonDiscovery(core_id)
server = discover.first()
discover.stop()
roonapi = RoonApi(appinfo, token, server[0], server[1], True)

prev_title = ""
prev_artist = ""
prev_album = ""

def main():
    while True:
        try:
            display_art()

        except KeyboardInterrupt:
            break

def display_art():

    import numpy as np
    zones = []

    zones = roonapi.zones

    prev_title = ""
    prev_artist = ""
    prev_album = ""

    for output in zones.values():
        # Found the zone information we are using

        displaying_art = "N"
        if output["display_name"] == target_zone:

            # If we are playing something then we should display the cover art on our device
            if output["state"] == "playing":
                while True:
                    # Extract the now playing information from the big output tuple
                    now_playing = output["now_playing"]
                    title = now_playing["three_line"]["line1"]
                    artist = now_playing["three_line"]["line2"]
                    album = now_playing["three_line"]["line3"]
                    displaying_art = "Y"
                    if prev_album.strip() != album.strip():
                        prev_album = album
                        print(f"Album {repr(album)} previous album {repr(prev_album)}")
                        # Get the image key and then use that to get the URL for the art being displayed
                        image_key = now_playing.get("image_key")

                        if image_key:
                            image_url = roonapi.get_image(image_key)
                            # Pull the actual picture
                            if image_url:

                                # Pull the image from the link
                                image_roon = Image.open(urlopen(image_url))

                                print(f"Processing image variable and converting to {target_size} BMP...")
                                img = image_roon.resize(target_size, Image.Resampling.LANCZOS)
                                img = img.convert("RGB") # Forces standard 24-bit uncompressed format

                                data = bytearray()
                                for r, g, b in img.getdata():
                                    data.extend([r, g, b])
                                img.close()
                                del img
                                # Retrieve the full raw byte array and its total size
                                print(f"At {time.strftime("%c")} sending in-memory bmp ({len(data)} bytes) to {pico_ip}:{port}...")
                                send_to_pico(data)

                    sleep(1.7)
                    if output["state"] != "playing":
                        # We have stopped playing music so send a blank image to the 
                        # Pico2 W which will clear down the art which was previously
                        # being displayed
                        arr = np.zeros((int(basewidth), int(basewidth), 3), dtype=np.uint8)
                        img = Image.fromarray(arr)
                        data = bytearray()
                        for r, g, b in img.getdata():
                            data.extend([r, g, b])
                        img.close()
                        del img

                        print(f"At {time.strftime("%c")} sending in-memory bmp (a blank) ({len(data)} bytes) to {pico_ip}:{port}...")
                        send_to_pico(data)

                        break
            sleep(1.7)

def send_to_pico(data):

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((pico_ip, port))
            header = struct.pack("<4sI", b"BMP1", len(data))
            sock.sendall(header + data)
    finally:
        del data
        gc.collect()


main()
