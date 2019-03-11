# meteoroPi
Estación Metereologica basada en Raspberry Pi, diseñada para capturar datos de estaciones metereologicas Davis ademas de capturas de camaras como la AllSky.

Sensore Usados:
- Davis Vantage Pro 2
- Camara Web USB / Capturador de video

Los sensores:

Los equematicos de las conexiones:

La informacion es almacenada en:
- Imagenes en formato PNG y JPG
- Archivos .CSV con los datos de la estacion metereologica

Codigo vidualizacion... en proceso.



# Problemas Actuales:

# Contents
Name | Description
-----|------------
`bom.md` | Bill of Materials - List of parts, counts, approximate prices and where to find.
`schematics/`| Fritzing Schematics for electronics
`station-code/`| Python3 Code.
`station-code/collectweather.py`| Main code for collecting weather data.
`README.md`|This file
`LICENSE`|Apache 2.0 License
`frontend/`| Docker container from running PHP scripts to display the data.
`structure.sql` | Postgresql Data schema.



# Pi Setup
- apt-get update
- apt-get upgrade
- apt-get dist-upgrade
- apt-get autoremove
- Turn on Interfacing Options:
    - SPI
    - I2C
    - 1-wire


# Python Packages
- sudo apt-get install libyaml-dev

# Postgresql Setup
- sudo apt-get install postgresql-9.6
- apt install postgresql libpq-dev postgresql-client postgresql-client-common
- sudo update-rc.d postgresql enable
- sudo su postgres
- createuser weatherstation -P --interactive
- createdb weatherstation
- create table using structure.sql
- GRANT ALL PRIVILEGES ON TABLE weatherdata TO weatherstation;
- https://www.howtoforge.com/tutorial/postgresql-replication-on-ubuntu-15-04/

# 3rd Party Sensor Modules:
Add SSH key:
```
eval $(ssh-agent -s)
ssh-add ~/.ssh/other_id_rsa
```
Checkout Modules, run sudo python setup.py install
```
git clone https://github.com/PrzemoF/bmp183.git
git clone git://gist.github.com/3151375.git
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
git clone https://github.com/adafruit/Adafruit_Python_MCP3008.git
```

Docker testing image:
```
docker build -t gitlab:4567/lab-projects/raspberry-pi-weatherstation .
```

# Components
- Leverages gitlab and pipelines to do tasks
- Started with Database is Postgresql and the pgadmin interface to get GUI
representation.



# License and Authors

Author::  ([@](https://))

Not Yet
