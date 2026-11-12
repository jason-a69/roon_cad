#!/bin/bash

# First of all, we need to get some information from the user.
# 1. What zone is the Pi in they are setting up
# 2. Which output display are they using (sense hat or Waveshare 1.5# LCD etc)

echo " "
echo "*** Roon Cover Art Display setup script *** "
echo " "
echo ""
echo "The current user will be setup to run this service"
echo " "
if [[ $EUID -eq 0 ]]; then
    echo "Do not run this as the root user"
    echo "Exiting"
    exit 1
fi
echo " "
echo "** This script will reboot the Pi at the end of the installation **"
echo " "
echo " "
echo "I need 2 things from you to setup this script"
echo " "
echo "I need to know which Roon zone the Pi will be in and I also need to know"
echo "which display you will be using"
echo " "
echo "(You can stop this script with CTRL-C)"
echo " "
echo "Will you be running this on a display attached to the Pi or to a remote Pico?"
echo " "
echo "Enter 1 for a local Raspberry Pi or 2 for a Raspberry Pico connected to your network"
read -r n_local_or_pico
c_local_or_pico=""
case $n_local_or_pico in
1)
  c_local_or_pico="L"
  ;;
2)
  c_local_or_pico="P"
  ;;
*)
  echo " "
  echo "Questions not answered, exiting"
  exit
esac
echo " "
echo "Please enter you Roon zone : "
read -r c_roon_zone
echo " "
if [[ "$c_local_or_pico" = "L" ]]; then
    echo "Please enter 1 for a sense hat, 2 for Waveshare 1.5 LCD (SKU 14747) or 3 for 2 inch TFT: "
    read -r c_display_number
    case $c_display_number in
      1)
        c_display_type="sense"
        ;;
      2)
        c_display_type="ws1in5"
        ;;
      3)
        c_display_type="2.0TFT"
        ;;
    esac
    echo "You display type is : " "$c_display_type"
elif [[ "$c_local_or_pico" = "P" ]]; then
    echo " "
    echo "Please enter the IP address of your Pico " 
    read -r c_pico_ip
    echo " "
    echo "Please enter the width of tbe display attached to your Pico " 
    read -r c_pico_width
    echo " "
else
    echo "Questions not answered, exiting"
    exit # Exit if questions are not answered
fi
echo ""
echo "Your zone is : " "$c_roon_zone"
echo ""
sleep 2
echo ""
echo "Installing software"
echo ""

sudo apt install -y python3-pip python3-dev p7zip-full gpiod libgpiod-dev python3-pil python3-spidev \
 python3 python3-venv 
pip3 install roonapi pillow numpy tomli-w --break-system-packages

case "$(uname -m)" in
    x86_64)
        echo "Running on 64-bit Intel/AMD (x86_64)"
        # Your x86_64 logic here
        ;;
    aarch64|armv6l|armv7l)
        echo "Running on Raspberry Pi (Aarch64/armv6l/armv7l)"
        # Your ARM logic here
        sudo apt install -y sense-hat python3-lgpio python3-rpi.gpio gcc-arm-linux-gnueabihf build-essential
        pip3 install RPi.GPIO spidev smbus gpiod --break-system-packages
        ;;
    i386|i686)
        echo "Running on 32-bit Intel/AMD (x86)"
        ;;
    *)
        echo "Unknown architecture: $(uname -m)"
        ;;
esac

case $c_display_number in
  2)
    sudo wget https://www.waveshare.com/w/upload/2/2c/OLED_Module_Code.7z
    7z x OLED_Module_Code.7z -O./OLED_Module_Code
    sudo cp -r ./OLED_Module_Code/RaspberryPi/python/lib/waveshare_OLED /usr/local/bin/.
    sudo chown -R "$USER" /usr/local/bin/waveshare_OLED
    echo ""
    echo "Checking /boot/firmware/config.txt for required parameters, changing if required"
    sudo bash -c 'grep -qxF 'dtparam=spi=on' /boot/firmware/config.txt || sudo echo 'dtparam=spi=on' >> /boot/firmware/config.txt'
    ;;
  3)
        sudo bash -c 'grep -qxF 'dtparam=spi=on' /boot/firmware/config.txt || sudo echo 'dtparam=spi=on' >> /boot/firmware/config.txt'
    ;;
esac
sleep 2
if [[ "$c_local_or_pico" = "L" ]]; then
    echo " "
    echo "Copying main program into place"
    echo ""
    sudo cp ./roon_cad_local.py /usr/local/bin/.
    sudo chown "$USER" /usr/local/bin/roon_cad_local.py
    sudo cp ./xytft.py /usr/local/bin/.
    sudo chown "$USER" /usr/local/bin/xytft.py
    sleep 2
#
#   Now test to see if service files exists, if it does, stop it and disable it.
#
    if [ -f /lib/systemd/system/roon_cad_local.service ]
    then
      echo ""
      echo "roon_cad_local service files exists already, stopping and disabling the service"
      echo ""
      sleep 2
      sudo systemctl stop roon_cad_local
      sudo systemctl disable roon_cad_local
      sudo mv /lib/systemd/system/roon_cad_local.service /lib/systemd/system/roon_cad_local.service_"$(date +%F-%T)"
      sleep 2
    fi
    echo "Patching the service file with current user information "
    echo ""
    sed -i "0,/User=/{s/User=.*/User=${USER}/}" ./roon_cad_local.service
    sleep 2
    echo ""
    echo "Moving service into place and enabling it"
    echo ""
    sudo cp roon_cad_local.service /lib/systemd/system/roon_cad_local.service
    sudo systemctl daemon-reload
    sudo systemctl enable roon_cad_local


  elif [[ "$c_local_or_pico" = "P" ]]; then
      echo " "
    echo "Copying main program into place"
    echo ""
    sudo cp ./roon_cad_pico.py /usr/local/bin/.
    sudo chown "$USER" /usr/local/bin/roon_cad_pico.py
    sleep 2
#
#   Now test to see if service files exists, if it does, stop it and disable it.
#
    if [ -f /lib/systemd/system/roon_cad_pico.service ]
    then
      echo ""
      echo "roon_cad_pico service files exists already, stopping and disabling the service"
      echo ""
      sleep 2
      sudo systemctl stop roon_cad_pico
      sudo systemctl disable roon_cad_pico
      sudo mv /lib/systemd/system/roon_cad_pico.service /lib/systemd/system/roon_cad_pico.service_"$(date +%F-%T)"
      sleep 2
    fi
    echo "Patching the service file with current user information "
    echo ""
    sed -i "0,/User=/{s/User=.*/User=${USER}/}" ./roon_cad_pico.service
    sleep 2
    echo ""
    echo "Moving service into place and enabling it"
    echo ""
    sudo cp roon_cad_pico.service /lib/systemd/system/roon_cad_pico.service
    sudo systemctl daemon-reload
    sudo systemctl enable roon_cad_pico
fi

case "$(uname -m)" in
    aarch64|armv6l|armv7l)
        echo ""
        echo "Adding current user to groups required to access LED displays"
        echo ""
        sudo usermod -a -G video,input,spi,gpio "$USER"
        sleep 2
        ;;
esac
if [ -d /etc/roon ]; then
  echo ""
  echo "Roon directory exists, no need to authorise the service in the roon app ... continuing ..."
  echo ""
  sleep 2
else
  echo ""
  echo "Setting up the Roon app"
  echo "You will need to open the Roon app on your device and enable roon_cad_local or roon_cad_pico in settings / extensions"
  echo "Press any key to continue " 
  read -r c_dummy
  echo ""
  sleep 2
  sudo mkdir -p /etc/roon
  sudo touch /etc/roon/config.toml
  sudo chmod 777 /etc/roon/config.toml
  echo ""
  sleep 2
  python3 ./discovery.py "$c_local_or_pico"
  echo "target_zone = \"$c_roon_zone\"" >> /etc/roon/config.toml
  if [[ "$c_local_or_pico" = "L" ]]; then
    echo "[local]" >> /etc/roon/config.toml
    echo "display_type = \"$c_display_type\"" >> /etc/roon/config.toml
  elif [[ "$c_local_or_pico" = "P" ]]; then
    echo "[pico]" >> /etc/roon/config.toml
    echo "ip = \"$c_pico_ip\"" >> /etc/roon/config.toml
    echo "basewidth = \"$c_pico_width\"" >> /etc/roon/config.toml
    echo "port = 5000" >> /etc/roon/config.toml
    echo " "
  fi
fi
echo " "
echo "Need to reboot, doing that now"
echo " "
sleep 5
sudo reboot