#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back h

#set nLaun1=launcher.sh
#set nLaun2=launcherWeb.sh

#set

#chmod 755 launcher.sh

# Cambiar uso de cronetab por otro que permita instalacion por consola
#sudo crontab -e
#echo "@reboot sh /home/pi/meteoroPi/Arranque/launcher.sh > /home/pi/meteoroPi/Arranque/logs/cronlog.txt 2>&1" >>
#echo "@reboot sh /home/pi/meteoroPi/Arranque/launcherWeb.sh > /home/pi/meteoroPi/Arranque/logs/cronlogWeb.txt 2>&1" >>


# Se activa el apagado por puerto raspberry (deve ser agregado en /etc/rc.local antes del exit!)
#sudo apt-get install pycd me    thon-dev python-rpi.gpiocd meteoroPi
#sudo sed  "/exit 0/ { N; exit 0\n/python /home/pi/meteoroPi/botonApagado/off_button.py & \n &/ }" /etc/rc.local
#sudo echo "python /home/pi/meteoroPi/botonApagado/off_button.py &" >> /etc/rc.local
#sudo echo "sh /home/pi/meteoroPi/arranque/launcher.sh >> /home/pi/meteoroPi/Arranque/logs/log.txt &" >> /etc/rc.local
#sudo echo "sh /home/pi/meteoroPi/arranque/launcherWeb.sh > /home/pi/meteoroPi/Arranque/logs/logWeb.txt &" >> /etc/rc.local