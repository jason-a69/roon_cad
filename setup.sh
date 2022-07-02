#!/bin/bash

# First of all, we need to get some information from the user.
# 1. What zone is the Pi in they are setting up
# 2. Which output display are they using (sense hat or Waveshare 1.5# LCD)

echo " "
echo " *** Roon Cover Art Display setup script *** "
echo " "
echo ""
echo " The current user will be setup to run this service"
echo " "
echo "** IF YOU ARE ROOT THEN LOG OUT AND LOG IN AS A NORMAL USER **"
echo " "
echo " "
echo " I need 2 things from you to setup this script"
echo " "
echo " I need to know which Roon zone the Pi will be in and I also need to know"
echo " which LED display you will be using"
echo " "
echo "(You can stop this script with CTRL-C)"
echo " "
read -p "Please enter you Roon zone : " c_roon_zone
read -p "Please enter 1 for a sense hat or 2 for Waveshare 1.5 LCD (SKU 14747) : " c_display_type
case $c_display_type in
  1)
    c_display_name="sense"
    ;;
  2)
    c_display_name="ws1in5"
    ;;
esac
echo ""
echo "Your zone is : " $c_roon_zone
echo "You display type is : " $c_display_name
echo ""
sleep 2
echo ""
echo "Installing software"
echo ""
sudo apt install -y python3-pip
pip3 install roonapi
case $c_display_type in
  1)
    sudo apt install -y sense-hat
    ;;
  2)
    pip3 install pillow numpy RPi.GPIO spidev smbus
    sudo apt-get install -y p7zip-full
    sudo wget https://www.waveshare.com/w/upload/2/2c/OLED_Module_Code.7z
    7z x OLED_Module_Code.7z -O./OLED_Module_Code
    sudo cp OLED_Module_Code/RaspberryPi/python/lib/waveshare_OLED /usr/local/bin/.
    sudo chown -R $USER /usr/local/bin/waveshare_OLED
    echo ""
    echo "Checking /boot/config.txt for required parameters, changing if required"
    grep -qxF 'dtparam=spi=on' /boot/config.txt || echo 'dtparam=spi=on' >> /boot/config.txt
    ;;
esac
sleep 2
echo "Patching the main program"
echo ""
sed -i "0,/target_zone =/{s/target_zone =.*/target_zone = \"${c_roon_zone}\"/}" ./roon_cad.py
sed -i "0,/display_type =/{s/display_type =.*/display_type = \"${c_display_name}\"/}" ./roon_cad.py
sleep 2
#
echo ""
echo "Copying main program into place"
echo ""
sudo cp ./roon_cad.py /usr/local/bin/.
sudo chown $USER /usr/local/bin/roon_cad.py
sleep 2
#
# Now test to see if service files exists, if it does, stop it and disable it.
#
if [ -f /lib/systemd/system/roon_cad.service ]
then
  echo ""
  echo "roon_cad service files exists already, stopping and disabling the service"
  echo ""
  sleep 2
  sudo systemctl stop roon_cad
  sudo systemctl disable roon_cad
  sudo mv /lib/systemd/system/roon_cad.service /lib/systemd/system/roon_cad.service_"$(date +%F-%T)"
  sleep 2
fi
echo ""
echo "Patching the service file with current user information "
echo ""
sed -i "0,/User=/{s/User=.*/User=\"${USER}\"/}" ./roon_cad.service
sleep 2
echo ""
echo "Moving service into place and enabling it"
echo ""
sudo cp roon_cad.service /lib/systemd/system/roon_cad.service
sudo systemctl daemon-reload
sudo systemctl enbable roon_cad
sleep 2
echo ""
echo "Adding current user to groups required to access LED displays"
echo ""
sudo usermod -a -G video,input,spi,gpio $USER
sleep 2
if [ -f /etc/roon_cad ]
then
  echo ""
  echo "roon_cad directory exists, no need to authorise the service in the roon app ... continuing ..."
  echo ""
  sleep 2
else
  echo ""
  echo "Setting up the Roon app"
  echo ""
  sleep 2
  sudo mkdir -p /etc/roon_cad
  sudo touch /etc/roon_cad/my_core_id_file
  sudo touch /etc/roon_cad/my_token_file
  sudo chmod 777 /etc/roon_cad/my_core_id_file
  sudo chmod 777 /etc/roon_cad/my_token_file
  echo ""
  echo "About to the run the discovery program, please authorise the roon_cad extension in"
  echo "the Roon app when prompted"
  echo ""
  sleep 2
  python3 ./discovery.py
  sleep 2
fi