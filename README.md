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
  
Clone this repository 

`git clone https://github.com/jason-a69/roon_cad`

`cd roon_cad`

`chmod +x setup.sh`

Run the setup script

`./setup.sh`

After a reboot...

Play some music in the correct zone and your display should light up 

When you stop the music the display should turn off

Enjoy!
