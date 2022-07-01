# roon_ca
Roon cover art display on 
1. sense hat (https://www.raspberrypi.com/products/sense-hat/)
2. Waveshare 1.5" (https://www.waveshare.com/1.5inch-rgb-oled-module.htm)
## Prerequisites

A Roon audio subscription

### Hardware 
  - a display listed above
  - a Raspberry Pi (I used a Pi 0 V1)
  
### Software
  - Dietpi (www.dietpi.com) I used V6 Bullseye (Raspian should work without any trouble).
  
### Additional software installed and instructions  
  `sudo apt install sense-hat python3-pip`
  
and then as user dietpi
  
`pip3 install roonapi`

Add dietpi user to video and input groups

`sudo addgroup dietpi video`

`sudo addgroup dietpi input`

(Logout and login again for changes to take effect)
  
Now create a new dirctory in /etc for roon information

`sudo mkdir -p /etc/roon`
  
Create configuration files

`sudo touch /etc/roon/my_core_id_file`

`sudo touch /etc/roon/my_token_file`

`sudo chmod 777 /etc/roon/my_core_id_file`

`sudo chmod 777 /etc/roon/my_token_file`
  
Download the repository

`git clone https://github.com/jason-a69/roon_ca`

`cd roon_ca`
  
Setup the files needed for Roon Audio (many thanks to https://github.com/pavoni/pyroon without his assistance this would not have been possible)

`python3 discovery.py`
   
Now go into you Roon app -  settings / Extensions and enable roon_ca_sense
   

Change the code to match your environment
You need to change line

`target_zone = "Qutest"`

in roon_ca_sense.py to match the zone where your Pi is
  
Copy the main program to /usr/local/bin

`sudo cp roon_ca_sense.py /usr/local/bin/.`
   
Copy the service file and enable and start it, if you are not using user dietpi then you will need to change line

`User = dietpi`

to the user you are using for your OS.

You also need to change the line

`ExecStart=/bin/bash -c '/usr/bin/python3 /usr/local/bin/roon_ca_sense.py'`

To the display you are using, the above example assumes the sense hat

Now copy the service file, enable and start it.

`sudo cp roon_ca.service /lib/systemd/system/.`

`sudo systemd daemon-reload`

`sudo systemd enable roon_ca`

`sudo systemd start roon_ca`
  
Check everything is running with

`sudo systemctl status roon_ca`
  
Play some music in the correct zone and your display should light up

When you stop the music the sense hat display should turn off
  
Enjoy!
