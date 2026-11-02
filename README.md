# roon_cad
Roon cover art display
1. Sense Hat (https://www.raspberrypi.com/products/sense-hat/)
2. Waveshare 1.5" (https://www.waveshare.com/1.5inch-rgb-oled-module.htm)
3. 2# TFT (something like this # https://www.alibaba.com/product-detail/2-0-inch-TFT-LCD-LCD_1601295816403.html
)

## Prerequisites

1. You will need a Roon audio subscription
2. If you are running on a locally attached device then you need a Pi. If you sending an image to a 
   Pico2W then you can run it on any Linux box that runs on the same subnet as the Pico2W


### Hardware 
  - One of the displays listed above
  - a Raspberry Pi (I used a Pi 0 V1)
  
### Software
  - Dietpi (www.dietpi.com) (Raspian should work without any trouble).
  
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
