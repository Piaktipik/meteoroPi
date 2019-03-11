
#!/bin/python


###################################### Librerias ##################################################
import os
from time import gmtime, strftime, localtime, strptime, time, sleep#, timedelta
import RPi.GPIO as GPIO
import gps as gp
import threading
import serial
import csv

###################################### Parametros Codigo ##################################################
# Parametros codigo:
tcap = 30 # Tiempo caputura fotogramas en segundos
tencap = 30 # Tiempo entre capturas en segundos
    
# Contador capturas
rutaCon = "/home/pi/allSky/conteo.txt"
rutaLog = "/home/pi/allSky/logSkyCam.txt"
rutaLogD = "/home/pi/allSky/davisLog/DavisLog.txt"

Nombres = ['L','O','O','Bar Trend','Packet Type','Next Record','Barometer','Inside Temperature','Inside Humidity','Outside Temperature','Wind Speed','10 Min Avg Wind Speed','Wind Direction','Extra Temperatures','Soil Temperatures','Leaf Temperatures','Outside Humidity','Extra Humidties','Rain Rate','UV','Solar Radiation','Storm Rain','Start Date of current Storm','Day Rain','Month Rain','Year Rain','Day ET','Month ET','Year ET','Soil Moistures','Leaf Wetnesses','Inside Alarms','Rain Alarms','Outside Alarms','Extra Temp/Hum Alarms','Soil & Leaf Alarms','Transmitter Battery Status','Console Battery Voltage','Forecast Icons','Forecast Rule number','Time of Sunrise','Time of Sunset','<LF> = 0x0A','<CR> = 0x0D','CRC']
Doff    = [1, 2, 3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 17, 19, 26, 30, 34, 35, 42, 44, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 67, 71, 72, 73, 75, 83, 87, 88, 90, 91, 92, 94, 96, 97, 98]
Dsize   = [1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 1, 1, 2, 7, 4, 4, 1, 7, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 1, 1, 2, 8, 4, 1, 2, 1, 1, 2, 2, 1, 1, 2]
DFact   = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]  
DSave   = [0,0,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
TamD = len(Nombres)

###################################### Variables ##################################################                
# variables captura tiempo 

tiempoS = [2000, 0, 0, 0, 0, 0]
tiempoG = [2000, 0, 0, 0, 0, 0]
tiempo = [2000, 0, 0, 0, 0, 0]
stopT1 = False

###################################### Puertos ###################################### 
led_rojo = 19
led_amar = 13
led_verd = 6
ena_easy = 12

GPIO.setmode(GPIO.BCM)

GPIO.setup(led_rojo, GPIO.OUT)
GPIO.setup(led_amar, GPIO.OUT)
GPIO.setup(led_verd, GPIO.OUT)
GPIO.setup(ena_easy, GPIO.OUT)

#puertoSerial = '/dev/ttyUSB0'
puertoSerial = '/dev/ttyACM0'
gpsInstalado = True

###################################### Funciones ##################################################
def mix2bytes(datosE,pos):
  return ord(datosE[pos + 1]) * 256 + ord(datosE[pos])

# Registro suscesos en Txt y consola
def regLog(texto):
    print (texto)
    fileL = open(rutaLog, "a")   # se crea el archivo 
    fileL.write(texto + '\n') 
    fileL.close() 

# Verificacion rutas guardado archivos
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

# Actualizamos tiempo sistema
def actualizarTiempo():
    # Extraemos tiempo sistema
    tiempoS[0] = int(strftime("%Y", localtime()))
    tiempoS[1] = int(strftime("%m", localtime()))
    tiempoS[2] = int(strftime("%d", localtime()))
    tiempoS[3] = int(strftime("%H", localtime()))
    tiempoS[4] = int(strftime("%M", localtime()))
    tiempoS[5] = int(strftime("%S", localtime()))

    # Tomamos el mayor de los tiempos entre Sistema y GPS
    for i in range(0,6):
        if tiempoS[i] < tiempoG[i]: # tiempo sistema menor que gps, actualizamos
            tiempo = tiempoG
            return tiempo
        if tiempoS[i] > tiempoG[i]: # tiempo sistema mayor que gps, actualizamos
            tiempo = tiempoS
            return tiempo
    return tiempoS

# hilo de captura tiempo GPS
def worker():
    """funcion que realiza el trabajo en el thread"""
    #Listen on port 2947 (gpsd) of localhost
    session = gp.gps("localhost", "2947")
    session.stream(gp.WATCH_ENABLE | gp.WATCH_NEWSTYLE)

    while True:
        try:
            report = session.next() # congela la ejecucion!
            # Wait for a 'TPV' report and display the current time
            # To see all report data, uncomment the line below
            # print report
            if report['class'] == 'TPV':
                if hasattr(report, 'time'):
                    tiempoG[0] = int(report.time[:4])
                    tiempoG[1] = int(report.time[5:7])
                    tiempoG[2] = int(report.time[8:10])
                    tiempoG[3] = int(report.time[11:13])
                    tiempoG[4] = int(report.time[14:16])
                    tiempoG[5] = int(report.time[17:19])
                    #print(tiempoG)

            if stopT1:
                break

        except KeyError:
            pass
        except KeyboardInterrupt:
            quit()
        except StopIteration:
            session = None
            regLog("GPSD has terminated")
    return

# hilo Captura datos Estacion
def capturaEstacion():
    ###################################### Guardamos Datos Estacion
    serialOperativo = False
    ultimoMinuto=0
    tiempo = actualizarTiempo()
    
    while(1):
        try:
            
            # si ultimo minuto fue capturado, esperamos el while
            while ultimoMinuto == tiempo[4]:
                tiempo = actualizarTiempo()
                sleep(1)
            
            if serialOperativo:
                
                while (ser.in_waiting > 0):
                    ser.read()
                regLog('Solicitando LOOP: ')
                ser.write(b'\n')
                ser.write(b'\n')
                sleep(0.1)
                ser.write(b'LOOP 1') 
                sleep(0.1)
                x = ser.read(100)          # read 99 bytes
                ser.flush()
                regLog('Lectura: ')
                regLog(x)

                # Creamos sistema de archivos
                ruta = '/home/pi/allSky/davisLog/A' + str(tiempo[0]) + 'M' + "%02d"%tiempo[1] + '/'
                ensure_dir(ruta)

                # Se carga el tiempo
                nombreArchivo = 'DatosEstacion' + str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2] 
                tiempoStr = str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2]  + ' ' + "%02d"%tiempo[3] + ':' + "%02d"%tiempo[4] + ':' + "%02d"%tiempo[5] 
                regLog("nCaptura... " + ruta + " T: " + tiempoStr)

                #Procesamos los datos Capturados
                #regLog('Procesando Datos: ')
                #regLog('# Datos Capturados' + str(len(x)))
                #xe = x.encode('ASCII') 
                Datos = [tiempoStr]     # Cargamos el tiempo como primera columna
                if len(x) > 99:
                    if(x[1]!='L'):      # Si el paquete llega con problema lo descartamos
                        continue
                        
                    for i in range(TamD):
                        aux = '0'
                        #regLog(Nombres[i] + ' Save:' +  str(DSave[i]) + ' * [' + str(DFact[i])+ ']')
                        if i<4:
                            aux = x[i] 
                        elif Dsize[i] < 2:
                            aux = str(ord(x[Doff[i]]))
                        else:
                            aux = str(mix2bytes(x,Doff[i]))
                        #regLog(aux)
                        # Agregamos Datos a salida
                        if DSave[i] == 1:
                            Datos.append(aux)
                else:
                    regLog('Captura Incompleta... Reintentando')
                    if serialOperativo:
                        continue
                

                #Guardamos los datos Capturados
                fileName = ruta + nombreArchivo + '.csv'
                try:
                    #regLog('Abriendo archivo...' + fileName)
                    open(fileName, 'rb')
                except:
                    # Archivo no existe, lo creamos
                    print('Error apertura... Creando archivo')
                    writer = csv.writer(open(fileName, 'w'))
                    # Cargamos nombres headers
                    headers = ['Tiempo Sistema'] # Cargamos el tiempo como primera columna
                    for i in range(TamD):
                        if DSave[i] == 1:
                            headers.append(Nombres[i])
                    regLog('Cabecera a escribir: ' + str(headers))
                    writer.writerow(headers)

                writer = csv.writer(open(fileName, 'a'))
                #regLog('Datos a escribir: ' + str(Datos))
                writer.writerow(Datos)
                regLog('Datos Guardados')
                # indicamos que ya se guardo datos para este minuto
                ultimoMinuto = tiempo[4]
                
            else:
                # inicializacion puerto Serial
                regLog('Iniciado Puerto... ' + puertoSerial)
                try:
                    if not gpsInstalado:
                        # forzamos la detencion del modulo del GPS que ocupa el puerto serial de la estacion
                        os.system(''' pgrep gpsd | awk '{system("sudo kill "$1)}' ''')
                    ser = serial.Serial(puertoSerial, 19200, timeout=5)
                    print(ser.name)
                    serialOperativo = True
                    regLog('Iniciado')
                except Exception as e:
                    serialOperativo = False
                    regLog('Error iniciando'+ str(e.message) + ' Argumentos: ' + str(e.args))
                    
        except Exception as e:
            regLog('Error Scrip Estacion: '+ str(e.message) + ' Argumentos: ' + str(e.args))

        # esperamos para realizar la proxima solicitud
        sleep(5)

# iniciamos hilo captura tiempo GPS
threads = list()
t = threading.Thread(target=worker)
threads.append(t)
t.start()

threads = list()
te = threading.Thread(target=capturaEstacion)
threads.append(te)
te.start()



###################################### Codigo principal ##################################################
try:
    
    regLog("Reiniciando EasyCap...")
    GPIO.output(ena_easy,GPIO.LOW) # Des-activamos capturado
    sleep(10)
    GPIO.output(ena_easy,GPIO.HIGH) # Activamos capturador

    ###################################### Inicio y Configuraciones ##################################################
    regLog("Inicio Script captura AllSky VLC")    
    GPIO.output(ena_easy,GPIO.HIGH) # Activamos capturador

    # Indicamos inicio programa (probamos leds)
    GPIO.output(led_rojo,GPIO.HIGH)
    sleep(1)
    GPIO.output(led_amar,GPIO.HIGH)
    sleep(1)
    GPIO.output(led_verd,GPIO.HIGH)
    sleep(1)
    GPIO.output(led_rojo,GPIO.LOW)
    sleep(1)
    GPIO.output(led_amar,GPIO.LOW)
    sleep(1)
    GPIO.output(led_verd,GPIO.LOW)
    regLog("Leds Iniciados") 
    
    # Conteo de capturas
    num = "1"
    try: # exepcion no existencia archivo
        file = open(rutaCon, "r")   
        num  = file.read() 
    except:
        file = open(rutaCon, "w+")   # se crea el archivo 
        file.write(num) 
        file.close() 
    cont = int(num)
    regLog("Conteo Cargado: " + str(num))


    # verificamos conexion y funcionamiento
    videoIn = 0
    maxVideo = 2
    esperar = True
    reiniciarE = 0      # permite reiniciar el capturador EasyCap
    reiniciarR = 0      # permite reiniciar la raspberry 

    # cerramos VLC
    os.system("sudo killall vlc")
    regLog("VLC Cerrado e inicio prog principal")

    ###################################### Programa principal ##################################################
    while(1):   
        try:
            tiempo = actualizarTiempo()
            regLog("Tsistema: " + str(tiempo))

            # Capturamos imagenes cada x tiempo
            if esperar: 
                regLog("Esperando... " + str(tencap) + ' Segundos')
                sleep(tencap)       # dormimos el resto de tiempo hasta timeEntreF
            else: 
                esperar = True      # activamos nuevamente la espera
            
            # Empiezo nueva captura 
            GPIO.output(led_verd,GPIO.LOW)

            # Creamos sistema de archivos
            ruta = '/media/pi/4D59-20AF/fotosCieloAllSky/A' + str(tiempo[0]) + 'M' + "%02d"%tiempo[1] + 'D' + "%02d"%tiempo[2] + '/' 
            #ruta = '/home/pi/Desktop/fotosCieloAllSky/A' + str(tiempo[0]) + 'M' + "%02d"%tiempo[1] + 'D' + "%02d"%tiempo[2] + '/' 
            ensure_dir(ruta)

            # Se carga el tiempo
            tiempoStr = str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2] + '-' + "%02d"%tiempo[3]+ '-' + "%02d"%tiempo[4]
            regLog("nCaptura... " + ruta + " T: " + tiempoStr)

            # Capturamos la lista de archivos antes de capturar
            listaOld = os.listdir(ruta) # Dir is your directory path
            number_filesOld = len(listaOld) # Le sumamos 1 para garantizar que se guardaron almenos 2 archivos
            
            # Iniciamos VLC
            GPIO.output(led_amar,GPIO.HIGH)
            #regLog("Iniciando VLC... ")
            #os.system("vlc v4l2:///dev/video" + str(videoIn) + " :v4l2-standard= :live-caching=3000 --scene-path=" + str(ruta) + " --scene-prefix=" + tiempoStr + "-C" + str(cont) + "_ &")
            regLog("Capturando imagen... ")
            os.system("fswebcam  -d /dev/video" + str(videoIn) + "  -r 800x600 -p JPEG  -q --no-banner " + str(ruta) + tiempoStr + "-C" + str(cont) + ".jpg")
            
            # Esperamos que capture un par de escenas
            #regLog("Capturando... " + str(tcap) + ' Segundos')
            sleep(tcap)		#dormimos el resto de tiempo hasta timeEntreF

            # Cerramos VLC
            #os.system("sudo killall vlc")
            GPIO.output(led_amar,GPIO.LOW)
            #sleep(2) # Esperamos unos segundos que cierre
            
            # reiniciamos indicadores
            GPIO.output(led_rojo,GPIO.LOW)

            # Actualizamos el contador de captura
            cont = cont + 1
            file = open(rutaCon,"w") 
            file.write(str(cont)) 
            file.close() 

            ## verificamos que este guardando si no cambiamos puerto de video y reintentamos de inmediato
            # tomamos la primera lista de archivos creados para remover los vacios!
            lista = os.listdir(ruta) # dir is your directory path
            number_files = len(lista)

            # verificamos tamano archivos generados, removemos los vacios
            for i in lista:
                statinfo = os.stat(ruta + "/" + i)
                tamFile = statinfo.st_size

                # Removemos los Vacios
                if tamFile<10000:
                    os.system("sudo rm " + ruta + "/" + i)

            # Cargamos de nuevo la lista de archivos creados aparentemente (tamano) validos
            lista = os.listdir(ruta) # dir is your directory path
            number_files = len(lista)

            regLog("Archivos nuevos detectados... " + str(number_files - number_filesOld))

            if number_files < (number_filesOld + 1):
                videoIn = (videoIn + 1) % maxVideo
                regLog("Falla video, probando otro puerto: " + str(videoIn))
                GPIO.output(led_rojo,GPIO.HIGH)
                cont = cont - 1     # Reiniciamos la captura anterior
                esperar = False     # Intentamos capturar de inmediato
                reiniciarE = reiniciarE + 1


                if reiniciarE > 3:
                    GPIO.output(led_rojo,GPIO.HIGH)
                    regLog("Reiniciando EasyCap...")
                    GPIO.output(ena_easy,GPIO.LOW) # Des-activamos capturador
                    sleep(10)
                    GPIO.output(ena_easy,GPIO.HIGH) # Activamos capturador
                    #os.system("sudo reboot")
                    reiniciarE = 0

                    

            else: # Imagenes generadas correctamente?
                GPIO.output(led_verd,GPIO.HIGH)
                reiniciarE = 0

            # Cerramos VLC
            print ("cerrando VLC... ")
            os.system("sudo killall vlc")
        except Exception as e:
            regLog('Error Scrip Captura: '+ str(e.message) + ' Argumentos: ' + str(e.args))


###################################### Fin codigo
except KeyError:
    GPIO.cleanup()
    quit()  

except KeyboardInterrupt:
    print("Saliendo")
    GPIO.cleanup()  # Revert all GPIO pins to their normal states (i.e. input = safe)
    os.system(''' pgrep python -n | awk '{system("sudo kill "$1)}' ''')
    quit()    



########################################### Cometarios ###############################################################################
#ruta = "/home/pi/Desktop/fotosCieloAllSky"
#ruta = '/home/pi/Desktop/fotosCieloAllSky/A' + strftime("%Y", localtime()) + 'M' + strftime("%m", localtime()) + 'D' + strftime("%d", localtime()) + '/' 
#tiempo = strftime("%Y-%m-%d-%H-%M", localtime()) 
# Reiniciamos Capturador
#os.system("./usbR1.sh")
#x = subprocess.check_output(['whoami'])
#print ("Nombre: " + i + " Size: " + str(tamFile) + " Valido: "+ str(tamFile>10000))
#print ("Removiendo: " + i )
#imagenes generadas
#procesarImagen(ruta)
#pass
#ruta = '/home/pi/Desktop/fotosCieloAllSky/' + strftime("%Y", localtime()) + '/' + strftime("%m", localtime()) + '/' + strftime("%d", localtime())
#ensure_dir(ruta)
# fecha actual
#tiempo = strftime("%Y-%m-%d-%H-%M-%S", localtime())

# comando busqueda de procesos con python 
# ps -ef | grep python
