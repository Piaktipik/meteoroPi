# meteoroPi
Estación Metereologica basada en Raspberry Pi, diseñada para capturar datos de estaciones metereologicas Davis ademas de capturas de camaras como la AllSky.

Sensores Soportados:
- Davis Vantage Pro 2
- Camara Web USB (compatible con fswebcam) / Capturador de video EasyCap / Raspberry Pi Camera

# Instalacion:

## Clonar repositorio en home
```sh
cd ~/
git clone https://github.com/Piaktipik/meteoroPi
```

## Activar archivos ejecutables e instalacion codigo (inicio automatico al reiniciar).
```sh
cd ~/meteoroPi
chmod +x Instalacion.sh
chmod +x codigoPrincipalHardware.py 
bash Instalacion.sh
```
## Seleccionar tipo de estacion a usar (Cambiar 0 por tipo de estacion, ver en tabla abajo)
```sh
nano ~/meteoroPi/config/estacion.txt
```

|         Tipo         | Capturador :GPS | :Davis |  :Arduino | : Caso | Descripcion       |
|:--------------------:|:---------------:|:------:|:---------:|--------|----------------------------------------------------------------------------|
|           0          |        no       |   :no  | :simulada | : no   | : Pruebas / Desarollo (requiere arduino para simular trama estacion Davis) |
|           1          |        no       |   :no  |   :real   | : no   | : ITM                                                                      |
|           2          |     :easycap    |   :si  |   :real   | : no   | : UdeA Oriente                                                             |
|           3          |       :no       |   :no  |    :no    | : si   | : Arduino                                                                  |
|           4          |      :Raspy     |   :no  |    :no    | : si   | : Arduino con RaspiCam                                                     |

## Instalar librerias
```sh
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install fswebcam
sudo apt-get install mencoder
sudo apt-get install gpsd gpsd-clients python3-gps pps-tools
sudo apt-get install screen
```

## Revisar USB conection with Davis
```sh
lsusb #-> (se deveria ver un dispositivo como -> Bus 001 Device 003: ID 10c4:ea60 Silicon Labs CP210x UART Bridge)
ls -l /dev/# -> lista los dispositivos, revisar al conectar y desconectar cual corresponde a la Davis -> algo como ttyUSB0
```

## Revisar USB serial Davis
```sh
screen /dev/ttyUSB0 19200
```

### Para solicitar un mensaje a la Davis teclear (incluir espacio y enter al final):
LOOP 1 -> si la estacion Davis esta operativa, la respuesta es algo como: LOO@u�A0����������������`������������������PKd
check codecs: https://docs.python.org/2.4/lib/standard-encodings.html

### Para cerrar SCREEN :
"Ctrl+a" y luego "\" seguido de yes "y"

## Mas informacion

Los equematicos de las conexiones y guia general:
https://docs.google.com/presentation/d/1L42o_n-11NsVIwM1Xeg_me6FlHfzaajuinyZlAdbweE/edit?usp=sharing

La informacion es almacenada en:
- Imagenes en formato PNG y JPG
- Archivos .CSV con los datos de la estacion metereologica seleccionada

Codigo vidualizacion... en proceso.

# Problemas Actuales:
Mejorar documentacion
Estabilizar version en modulos activos
Revisar compatibilidad con Python3
Actualizar instalaccion


# License and Authors

Author::  ([@](https://))

Not Yet
