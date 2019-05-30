#!/bin/sh

# Comandos arreglar USB
# movemos archivos de carpeta
sudo cp -r -f /media/pi/4D59-20AF/fotosCieloAllSky/* /media/pi/4D59-20AF1/fotosCieloAllSky/
sudo rm -r /media/pi/4D59-20AF/*
#sudo rsync -a /media/pi/4D59-20AF/ /media/pi/4D59-20AF1/
# Desmontamos y remontamos la USB
sudo umount /dev/sda1
sudo mount -t vfat /dev/sda1 /media/pi/4D59-20AF/ -o uid=1000
#sudo mount -t vfat /dev/sdb1 /media/pi/4D59-20AF/ -o uid=1000



# Otras:
#sudo cp -v -f /media/pi/4D59-20AF/fotosCieloAllSky/* /media/pi/4D59-20AF/fotosCieloAllSky/*
#sudo rm -r /media/pi/4D59-20AF
#sudo mkdir /media/pi/4D59-20AF
