
#!/bin/python
###################################### Librerias ##################################################
import os
from time import gmtime, strftime, localtime, strptime, time, sleep#, timedelta
import RPi.GPIO as GPIO
import gps as gp
import threading
import serial
import csv
import pwd

###################################### Parametros ##################################################
###################################### Parametros Estacion:
tipEstacion = 0 # Tipo de estacion (Por defecto pruebas)
# Tipo  :Capturador :GPS    :Davis      : Caso
# 0     :no         :no     :simulada   : Pruebas Julian
# 1     :no         :no     :real       : ITM
# 2     :easycap    :si     :real       : UdeA Oriente

tipoCapturador = [False,False,True] 
tipoGPS        = [False,False,True]
tipoDavis      = [False,True,True]

# Notas: GPS instalado en puerto serial GPIO raspberry

###################################### Parametros Muestreo:
tcap = 5 # Tiempo caputura fotogramas en segundos
tencap = 54 # Tiempo entre capturas en segundos

###################################### Parametros Nombres archivos:
# Se indican los nombres de los archivos 
# Archivos para almacenar informacion
arcConteo = "conteo"
arcEstacion = "estacion"
# Archivos log
arcLogCapturaImagen = "logCam"
arcLogCapturaDavis = "logDavis"

###################################### Parametros Rutas:
rutaMeteoroPi = "/home/pi/meteoroPi/"
rutaImagenes = "/media/pi/4D59-20AF"

carpetaConfigurciones = "config/"
carpetaLogs = "logs/"
carpetaDatos = "datos/"
carpetaImagenes = "fotosCieloAllSky/"

# Se definen las rutas de los archivos de configuracion
rutaCon = rutaMeteoroPi + carpetaConfigurciones + arcConteo + ".txt"
rutaEst = rutaMeteoroPi + carpetaConfigurciones + arcEstacion + ".txt"
# En estas rutas se guardan los logs
rutaLog = rutaMeteoroPi + carpetaLogs + arcLogCapturaImagen + ".txt"
rutaLogD = rutaMeteoroPi + carpetaLogs + arcLogCapturaDavis + ".txt"
# Se definen las rutas donde se guardan los datos
rutaDatos = rutaMeteoroPi + carpetaDatos 
rutaImg = rutaImagenes + "/" + carpetaImagenes

# Verificacion rutas guardado archivos
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
        uid =  pwd.getpwnam('pi').pw_uid
        os.chown(d, uid, uid) # set user and group
        
def ensure_USB(rUSB,f):
    pUSB = os.path.dirname(rUSB)
    d = os.path.dirname(f)
    if os.path.exists(pUSB):
        # USB conectada
        if not os.path.exists(d):
            # USB no conectada
            os.makedirs(d)
            uid =  pwd.getpwnam('pi').pw_uid
            os.chown(d, uid, uid) # set user and group
            #uid, gid =  pwd.getpwnam('pi').pw_uid, pwd.getpwnam('pi').pw_uid
            #os.chown(d, uid, gid) # set user:group as root:pi
    else:
        #Si usb no conectada
        regLog("USB: " + str(rUSB) + " no detectada")
        # Estrategia de almacenamiento alterna - reiniciar?

# Registro actividad en .txt y consola
def regLog(texto):
    print (texto)
    ensure_dir(rutaLog)
    fileL = open(rutaLog, "a")   # se crea el archivo 
    fileL.write(texto + '\n') 
    fileL.close()
    
def regLogD(texto):
    print (texto)
    ensure_dir(rutaLogD)
    fileL = open(rutaLogD, "a")   # se crea el archivo 
    fileL.write(texto + '\n') 
    fileL.close() 

###################################### Verificacion de tipo de estacion
try: # exepcion no existencia archivo
    file = open(rutaEst, "r")
    tipEstacionL  = file.read() 
    tipEstacion = int(tipEstacionL)
except:
    ensure_dir(rutaEst)
    file = open(rutaEst, "w+")   # Se crea el archivo 
    file.write(str(tipEstacion)) 
    file.close() 
regLog("Tipo Estacion Cargado: " + str(tipEstacion))


# Parametros estructura trama estacion Davis Vantage Pro 2:
Nombres = ['L','O','O','Bar Trend','Packet Type','Next Record','Barometer','Inside Temperature','Inside Humidity','Outside Temperature','Wind Speed','10 Min Avg Wind Speed','Wind Direction','Extra Temperatures','Soil Temperatures','Leaf Temperatures','Outside Humidity','Extra Humidties','Rain Rate','UV','Solar Radiation','Storm Rain','Start Date of current Storm','Day Rain','Month Rain','Year Rain','Day ET','Month ET','Year ET','Soil Moistures','Leaf Wetnesses','Inside Alarms','Rain Alarms','Outside Alarms','Extra Temp/Hum Alarms','Soil & Leaf Alarms','Transmitter Battery Status','Console Battery Voltage','Forecast Icons','Forecast Rule number','Time of Sunrise','Time of Sunset','<LF> = 0x0A','<CR> = 0x0D','CRC']
Doff    = [1, 2, 3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 17, 19, 26, 30, 34, 35, 42, 44, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 67, 71, 72, 73, 75, 83, 87, 88, 90, 91, 92, 94, 96, 97, 98]
Dsize   = [1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 1, 1, 2, 7, 4, 4, 1, 7, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 1, 1, 2, 8, 4, 1, 2, 1, 1, 2, 2, 1, 1, 2]
DFact   = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]  
DSave   = [0,0,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
TamD = len(Nombres)

###################################### Variables ##################################################                
# Variables captura tiempo 
tiempoS = [2000, 0, 0, 0, 0, 0]
tiempoG = [2000, 0, 0, 0, 0, 0]
tiempo = [2000, 0, 0, 0, 0, 0]
stopT1 = False

###################################### Puertos ###################################### 
# Puertos leds indicadores estado captura imagenes
led_rojo = 19
led_amar = 13
led_verd = 6
ena_easy = 12       # Puerto activacion capturador de video


GPIO.setmode(GPIO.BCM)          # Seleccionamos modo de identificacion de puertos BCM ( https://raspberrypi.stackexchange.com/questions/12966/what-is-the-difference-between-board-and-bcm-for-gpio-pin-numbering )
# Se configuran los puertos como salidas
GPIO.setup(led_rojo, GPIO.OUT)
GPIO.setup(led_amar, GPIO.OUT)
GPIO.setup(led_verd, GPIO.OUT)
GPIO.setup(ena_easy, GPIO.OUT)

# Identificamos el puerto USB estacion Davis
if tipoDavis[tipEstacion]:
    puertoSerial = ['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3']    # Davis Real
else:
    puertoSerial = ['/dev/ttyACM0','/dev/ttyACM1','/dev/ttyACM2','/dev/ttyACM3']    # Pruebas arduino

###################################### Funciones ##################################################
# Mezcla bytes de la trama entregada por la estacion Davis
def mix2bytes(datosE,pos):
  return ord(datosE[pos + 1]) * 256 + ord(datosE[pos])

# Actualiza tiempo sistema entre GPS (Si esta activo y tiempo sistema)
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


###################################### Hilos codigo
# Hilo de captura tiempo GPS
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

# Hilo Captura datos Estacion
def capturaEstacion():
    ###################################### Guardamos Datos Estacion
    serialOperativo = False     # Se entiende como inactiva la conexion con la estacion Davis
    ser = None                  # Limpiamos conexion comunicacion serial Davis
    ultimoMinuto=0              # Se inicializa variable usada para captura cada minuto
    tiempo = actualizarTiempo() # Se inicializa el tiempo del sistema
    
    nPuertoSerial = 0
    while(1):

        # Intentamos correr el codigo de captura de datos de la estacion Davis
        try:
            
            # Si ultimo minuto ya fue capturado, actualizamos el tiempo y esperamos
            while ultimoMinuto == tiempo[4]:
                tiempo = actualizarTiempo()
                sleep(1)

            # Pasado un minuto procedemos a solicitar un dato de la estacion
            if serialOperativo:
                # Si la comunicacion serial esta activa ->

                # Vaciamos buffer puerto Serial
                while (ser.in_waiting > 0):
                    ser.read()

                ###################################### Solicitamos una trama LOOP a la estacion:
                regLog('Solicitando LOOP: ')
                ser.write(b'\n')
                ser.write(b'\n')
                sleep(0.1)
                ser.write(b'LOOP 1') 
                sleep(0.1)
                # Leemos la trama LOOP 
                x = ser.read(100)          # read 99 bytes
                ser.flush()
                regLogD('Lectura: ')
                regLogD(x)

                # Creamos sistema de archivos para almacenar los datos de la estacion Davis:
                ruta = rutaDatos + 'davis/A' + str(tiempo[0]) + 'M' + "%02d"%tiempo[1] + '/'
                ensure_dir(ruta)

                ###################################### Se carga el tiempo 
                # En el nombre del archivo  en formato pandas YY-MM-DD HH:MM:SS
                nombreArchivo = 'DatosEstacion' + str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2] 
                # En formato pandas YY-MM-DD HH:MM:SS para la captura actual
                tiempoStr = str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2]  + ' ' + "%02d"%tiempo[3] + ':' + "%02d"%tiempo[4] + ':' + "%02d"%tiempo[5] 
                # Se reporta tiempo captura
                regLog("nCaptura... " + ruta + " T: " + tiempoStr + " Procesando trama...")

                ###################################### Procesamos los datos Capturados
                Datos = [tiempoStr]     # Cargamos el tiempo como primera columna
                # Se verifica que el tamano sea valido
                if len(x) > 99:
                    if(x[1]!='L'):      # Se verifica que el paquete inicie con L (de la trama LOOP)
                        continue        # Si no es correcto se solicita un nuevo paquete
                    
                    ###################################### Recorremos, y alistamos datos para almacenamiento
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
                    # Si no es correcto se solicita un nuevo paquete
                    regLog('# Datos < 100, Captura Incompleta... Reintentando')
                    continue
                
                # Si los datos tienen el inicio y cantidad correcta los guardamos
                ###################################### Guardamos los datos Capturados
                fileName = ruta + nombreArchivo + '.csv'
                 # Intentamos abrir archivo 
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
                    #regLog('Cabecera a escribir: ' + str(headers))

                    # Cargamos cabecera del .CSV
                    writer.writerow(headers)

                # Abrimos el archivo
                writer = csv.writer(open(fileName, 'a'))
                #regLog('Datos a escribir: ' + str(Datos))
                writer.writerow(Datos)
                regLog('Datos Guardados')

                # Todo salido bien!, indicamos que ya se guardo datos para este minuto
                ultimoMinuto = tiempo[4]
                
            # Si no hay conexion serial:
            else:
                # Se reporta el puerto a iniciar
                regLog('Iniciado Puerto... ' + puertoSerial[nPuertoSerial])
                try:
                    if not tipoGPS[tipEstacion]:
                        # Forzamos la detencion de la libreria GPS, ya que por defecto ocupa el puerto serial de la estacion
                        os.system(''' pgrep gpsd | awk '{system("sudo kill "$1)}' ''')
                    
                    # Se crea el puerto
                    ser = serial.Serial(puertoSerial[nPuertoSerial], 19200, timeout=5)
                    # Se reporta el puerto iniciado
                    regLog(ser.name)
                    serialOperativo = True
                    regLog('Iniciado')

                except Exception as e:
                    # Si ocurre un error iniciando el puerto serial, lo reportamos
                    serialOperativo = False
                    # Probamos otro puerto:
                    nPuertoSerial = (nPuertoSerial + 1) % len(puertoSerial)
                    regLog('Error iniciando: Argumentos: ' + str(e.args) + 'Probando puerto: '+ str(puertoSerial[nPuertoSerial]))
                    
                    
        except Exception as e:
            # Si ocurre un error general en el codigo de la estacion, lo reportamos
            regLog('Error Scrip Estacion: Argumentos: ' + str(e.args))

        # Esperamos para realizar la proxima solicitud
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
    if tipoCapturador[tipEstacion]:
        regLog("Reiniciando EasyCap...")
        GPIO.output(ena_easy,GPIO.LOW) # Des-activamos capturado
        sleep(10)
        GPIO.output(ena_easy,GPIO.HIGH) # Activamos capturador

    ###################################### Inicio y Configuraciones ##################################################
    ######################################  Indicamos inicio programa (probamos leds)
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
    
    ######################################  Conteo de capturas
    num = "1"
    try: # Exepcion no existencia archivo
        file = open(rutaCon, "r")   
        num  = file.read() 
    except:
        ensure_dir(rutaCon)
        file = open(rutaCon, "w+")   # Se crea el archivo 
        file.write(num) 
        file.close() 
    cont = int(num)
    regLog("Conteo Cargado: " + str(num))

    ######################################  Variables verificacion conexion y funcionamiento
    videoIn = 0
    maxVideo = 2
    esperar = True
    numCapturasFallidas = 0   # Permite reiniciar el capturador EasyCap y raspberry 

    ###################################### Programa principal ##################################################
    regLog(" -------------------- Inicio programa principal ------------------------ ")
    ultimoMinutoImagen=0              # Se inicializa variable usada para captura cada minuto
    tiempo = actualizarTiempo() # Se inicializa el tiempo del sistema

    while(1):   
        try:
            tiempo = actualizarTiempo()
            regLog("Tsistema: " + str(tiempo))

            # Capturamos imagenes cada x tiempo
            #if esperar: 
            #    regLog("Esperando... " + str(tencap) + ' Segundos')
            #    sleep(tencap)       # dormimos el resto de tiempo hasta timeEntreF
            #else: 
            #    esperar = True      # activamos nuevamente la espera
            
             # Si ultimo minuto ya fue capturado, actualizamos el tiempo y esperamos
            while ultimoMinutoImagen == tiempo[4]:
                tiempo = actualizarTiempo()
                sleep(1)

            # Empiezo nueva captura 
            GPIO.output(led_verd,GPIO.LOW)

            # Creamos sistema de archivos
            ruta =  rutaImg + 'A' + str(tiempo[0]) + 'M' + "%02d"%tiempo[1] + 'D' + "%02d"%tiempo[2] + '/' 
            ensure_USB(rutaImagenes,ruta)

            # Se carga el tiempo
            tiempoStr = str(tiempo[0]) + '-' + "%02d"%tiempo[1] + '-' + "%02d"%tiempo[2] + '-' + "%02d"%tiempo[3]+ '-' + "%02d"%tiempo[4]
            regLog("Capturando... " + ruta + " T: " + tiempoStr)

            # Capturamos la lista de archivos antes de capturar
            listaOld = os.listdir(ruta) # Dir is your directory path
            number_filesOld = len(listaOld) # Le sumamos 1 para garantizar que se guardaron almenos 2 archivos
            
            # Iniciamos Captura
            GPIO.output(led_amar,GPIO.HIGH)
            #regLog("Iniciando VLC... ")
            #os.system("vlc v4l2:///dev/video" + str(videoIn) + " :v4l2-standard= :live-caching=3000 --scene-path=" + str(ruta) + " --scene-prefix=" + tiempoStr + "-C" + str(cont) + "_ &")
            if tipoCapturador[tipEstacion]:
                regLog("Capturando imagen EasyCap... ")
                os.system("fswebcam  -d /dev/video" + str(videoIn) + "  -r 1920x1080 -S 40 -q --no-banner " + str(ruta) + tiempoStr + "-C" + str(cont) + ".jpg")
            else:
                regLog("Capturando imagen... ")
                os.system("fswebcam  -d /dev/video" + str(videoIn) + "  -r 1920x1080 -q --no-banner " + str(ruta) + tiempoStr + "-C" + str(cont) + ".jpg")
            
            
            
            # Esperamos que capture un par de escenas
            #regLog("Capturando... " + str(tcap) + ' Segundos')
            #sleep(tcap)		#dormimos el resto de tiempo hasta timeEntreF

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

                # Removemos los Vacios o defectuosos(< detemrinados bytes)
                if tipoCapturador[tipEstacion]:
                    if tamFile<50000:
                        os.system("sudo rm " + ruta + "/" + i)
                else:
                    if tamFile<50000:
                        os.system("sudo rm " + ruta + "/" + i)

            # Cargamos de nuevo la lista de archivos creados aparentemente (tamano) validos
            lista = os.listdir(ruta) # dir is your directory path
            number_files = len(lista)

            number_files = number_files - number_filesOld
            regLog("Archivos nuevos detectados... " + str(number_files))

            if number_files < 1:
                videoIn = (videoIn + 1) % maxVideo
                regLog("Falla video, probando otro puerto: " + str(videoIn))
                GPIO.output(led_rojo,GPIO.HIGH)
                cont = cont - 1     # Reiniciamos la captura anterior

                # Contador intentos fallidos de captura 
                numCapturasFallidas = numCapturasFallidas + 1

                if numCapturasFallidas > 3:
                    # Falla en captura leve
                    GPIO.output(led_rojo,GPIO.HIGH)
                    if tipoCapturador[tipEstacion]:
                        regLog("Reiniciando EasyCap...")
                        GPIO.output(ena_easy,GPIO.LOW) # Des-activamos capturador
                        sleep(10)
                        GPIO.output(ena_easy,GPIO.HIGH) # Activamos capturador

                # Se evita perder datos de la estacion preguntanto si ya fue capturado el ultimo minuto
                if numCapturasFallidas > 10 and False:
                    # Falla en captura permanente, reinicio Raspberry
                    os.system("sudo reboot")

                # Verificamos estado imagen 

            else: # Imagenes generadas correctamente?
                GPIO.output(led_verd,GPIO.HIGH)
                numCapturasFallidas = 0
                ultimoMinutoImagen = tiempo[4]


        except Exception as e:
            regLog('Error Scrip Captura: Argumentos: ' + str(e.args))


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
