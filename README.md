# roon_cad
Roon cover art display
1. Sense Hat (https://www.raspberrypi.com/products/sense-hat/)
2. Waveshare 1.5" (https://www.waveshare.com/1.5inch-rgb-oled-module.htm)

## Prerequisites

You will need a Roon audio subscription

### Hardware 
  - One of the displays listed above
  - a Raspberry Pi (I used a Pi 0 V1)
  
### Software
  - Dietpi (www.dietpi.com) I used V6 Bullseye (Raspian should work without any trouble).
  
### Additional software installed and instructions  
  `sudo apt install python3-pip`
  
and then as user dietpi
  
`pip3 install roonapi`

Add dietpi (or pi for Raspbian) to groups that are needed to use displays

`sudo usermod -a -G video,input,spi,gpio dietpi`

(Logout and login again for changes to take effect)
  
Now create a new dirctory in /etc for roon information

`sudo mkdir -p /etc/roon`
  
Create configuration files

`sudo touch /etc/roon/my_core_id_file`

`sudo touch /etc/roon/my_token_file`

`sudo chmod 777 /etc/roon/my_core_id_file`

`sudo chmod 777 /etc/roon/my_token_file`
  
Download the repository

`git clone https://github.com/jason-a69/roon_cad`

`cd roon_cad`
  
Setup the files needed for Roon Audio (many thanks to https://github.com/pavoni/pyroon) without his assistance this would not have been possible)

`python3 discovery.py`
   
Now go into you Roon app on your phone -  settings / Extensions and enable roon_cad
   
### Installation and setup guide for sense hat

Install the pip libraries needed

`sudo apt install sense-hat`

Changes to `roon_cad.py`

Change `Qutest` on line `target_zone = "Qutest"`  to match the zone where the Pi is

Copy the main program to /usr/local/bin

`sudo cp roon_cad.py /usr/local/bin/.`

### Installation and setup guide for Waveshare 1.5" (SKU 14747)

Install the pip libraries needed

`pip3 install pillow numpy RPi.GPIO spidev smbus`

Changes to `roon_cad.py`

Change `Qutest` on line `target_zone = "Qutest"`  to match the zone where the Pi is

Change this line `display_type = "sense"` to `display_type = "ws1in5"` 

Copy the main program to /usr/local/bin

`sudo cp roon_cad.py /usr/local/bin/.`

Now the hacks :( 

You need to download the python libraries from waveshare and copy them over to `/usr/local/bin`

`sudo apt-get install p7zip-full`

`sudo wget  https://www.waveshare.com/w/upload/2/2c/OLED_Module_Code.7z`

`7z x OLED_Module_Code.7z -O./OLED_Module_Code`

`sudo cp OLED_Module_Code/RaspberryPi/python/lib/waveshare_OLED /usr/local/bin/.`

`sudo chown -R dietpi /usr/local/bin/waveshare_OLED`

(substitute dietpi with pi if you are using Rasbian in the above line)

In `/boot/config.txt` make sure this is set `dtparam=spi=on`

Reboot the Pi for changes to take effect

### Service file setup
Changes to `roon_ca.service`

If you are not using user dietpi then you will need to change line

`User = dietpi`

to the user you are using for your OS (probably to pi if you are using Raspbian)

Now copy the service file, enable and start it.

`sudo cp roon_cad.service /lib/systemd/system/.`

`sudo systemd daemon-reload`

`sudo systemd enable roon_cad`

`sudo systemd start roon_cad`
  
Check everything is running with

`sudo systemctl status roon_ca`
  
Play some music in the correct zone and your sense hat should light up

When you stop the music the sense hat display should turn off

Enjoy!
