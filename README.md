# roon_ca_sense
Roon cover art display on sense hat

Prerequisites

A Roon audio subscription

Hardware 
  a sense hat
  a Raspberry Pi (I used a Pi 0 V1)
  
Software
  Dietpi (www.dietpi.com) I used V6 Bullseye
  (Raspian should work without any trouble).
  
Additional software installed and instructions  
  sudo apt install sense-hat python3-pip 
  and then as user dietpi
    pip3 install roonapi

Add dietpi user to video and input groups
  sudo addgroup dietpi video
  sudo addgroup dietpi input
  (Logout and login again for changes to take effect)
  
Now create a new dirctory in /etc for roon information
  sudo mkdir -p /etc/roon
And create configuration files
  sudo touch /etc/roon/my_core_id_file
  sudo touch /etc/roon/my_token_file
  sudo chmod 777 /etc/roon/my_core_id_file
  sudo chmod 777 /etc/roon/my_token_file
  
Download the code
  git clone https://github.com/jason-a69/roon_ca_sense
  cd roon_ca_sense
  
Setup the files needed for Roon Audio (many thanks to https://github.com/pavoni/pyroon without his assistance this would not have been possible)
   python3 discovery.py
   
   Now go into you Roon app -  settings / Extensions and enable roon_ca_sense
   
Change the code to match your environment
  You need to change line
  target_zone = "Qutest"
  in roon_ca_sense.py
  to match the zone where your Pi is
  
Copy the main program to /usr/local/bin
   sudo cp roon_ca_sense.py /usr/local/bin/.
   
Copy the service file and enable and start it, if you are not using use dietpi then you will need to change line
  User = dietpi
  to reflect that
  
  sudo cp roon_ca_sense.service /lib/systemd/system/.
  sudo systemd daemon-reload
  sudo systemd enable roon_ca_sense
  sudo systemd start roon_ca_sense
  
Check everything is running with
  sudo systemctl status roon_ca_sense
  
Play some music in the correct zone and your sense hat should light up

When you stop the music the sense hat display should turn off
  
