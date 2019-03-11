#!/usr/bin/env python
# -*- coding: utf-8 -*- 
#from __future__ import print_function
############################################################# Librerias #############################################################
# Flask (libreria servidor web)
from flask import Flask, render_template, g, redirect, url_for, request, make_response, flash

from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect

import eventlet
# monkey patching is necessary because this application uses a background thread
eventlet.monkey_patch()


# Librerias Auxiliares
import time
from RF24 import *
import RPi.GPIO as GPIO
import os
import serial
import json

# Base de Datos
from sqlite3 import dbapi2 as sqlite3
from interfaceTableMapping import Base, engine, Objetos, Funciones , Variables
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


############################################################# Variables Globales #############################################################

# Funciones Globales para el control del tiempo en ms
millis = lambda: int(round(time.time() * 1000)) # Obtenemos una base de reloj que emula la funcion millis en Arduino

# Variables para la deteccion de estado (conectado/desconectado) de los objetos padres
ultimaRevision = 0 				# variable para saber cuando se revisaron por ultima vez los modulos
objetosPadresCargados = None	# variable que contiene una lista con los objetos cargados en la base de datos
tiempoRespuestaObjetos = {}		# contiene los tiempos de respuesta de cada objeto
numPadrescargados = 0
# variables control de maximo numero de ejecusiones por tiempo
tiempoEntreFunciones = 1000
ultimoTiempoFuncion = 0

#################### configuracion Modulo Comunicacion NRF24L01 ######################

# RPi B2 - Setup for GPIO 22 CE and CE0 CSN for RPi B2 with SPI Speed @ 8Mhz
radio = RF24(RPI_BPLUS_GPIO_J8_15, RPI_BPLUS_GPIO_J8_24, BCM2835_SPI_SPEED_8MHZ)

#puertos de comunicacion por defecto de escucha y de envio respectivamente
pipes = [0xF0F0F0F0E1, 0xF0F0F0F0D2]

print('Inicio: Inf: Iniciando modulo NRF24L01')
radio.begin()
radio.setPALevel(RF24_PA_LOW)
radio.enableDynamicPayloads()
radio.setRetries(2,5)
radio.printDetails()

radio.openReadingPipe(1,pipes[0])
print('Inicio: Inf: Escuchando por direccion: {}'.format(pipes[0]))
radio.openWritingPipe(pipes[1])
print('Inicio: Inf: Enviando por direccion: {}'.format(pipes[1]))

# Escuchamos si hay algun modulo publicandose (escribiendo por el canal de escucha por defecto)
radio.startListening()

#################### configuracion Comunicacion Serial ######################

print('Inicio: Inf: Iniciando Recepcion Serial')
port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=0)


#################### Servidor Flask ###################### 
# creamos la aplicacion web
print('Inicio: Inf: Iniciando aplicacion')
app = Flask(__name__)
socketio = SocketIO(app)

#############################################################  Funciones ############################################################# 
#################### Funcion manejo Socketio ######################
@socketio.on('my event', namespace='/interface')
def test_message(message):
	global tiempoEntreFunciones, ultimoTiempoFuncion
	idPadre = message['data']['idPadreFun']
	nomFun = message['data']['nomFun']
	if millis()-ultimoTiempoFuncion > tiempoEntreFunciones:
		print("consulta id objeto: {}, Funcion: {}".format(idPadre,nomFun))
		informarEvento('Ejecutando Funcion {}'.format(nomFun))
		ejecutarFuncion(idPadre,nomFun)
		ultimoTiempoFuncion = millis()

#################### Funcion Principal que es corrida en el hilo ######################
def Interface():

	recargarObjetos()		# Recarga La lista de objetos padres, al inicio y cuando se agrega un nuevo objeto
	escucharModulos()		# Revisa si los objetos se estan comunicando
	revisarModulos()		# Envia PING y espera PONG, de no llegar le cambia el estado al modulo y lo informa
	time.sleep(0.05)		# pequeña pausa para no sobre cargar el procesador



#################### Funciones principales ######################
def recargarObjetos():
	global objetosPadresCargados, numPadrescargados

	if(objetosPadresCargados == None):
		numPadrescargados = 0
		objetosPadresCargados = cargarObjetosPadres()
		for objPad in objetosPadresCargados:
			numPadrescargados += 1
		print("recargarObjetos: Inf: Objetos Padres Cargados")

def escucharModulos():
	escucharModulosGuardados()
	escucharModulosNuevos()
	
def escucharModulosGuardados():
	global objetosPadresCargados

	if(objetosPadresCargados != None):			# si hay padres cargados en la base de datos
		for objPad in objetosPadresCargados:

			if objPad.DireccionTx != None:		# si el padre tiene direccion, es un modulo NRF24L01
				mensajeN = recivirMensajeNrf24l01(objPad.DireccionRx) # leemos a un modulo especifico y a la direccion por defecto
				if (mensajeN != ""):
					procesarMensajeNrf24l01(objPad.id, mensajeN, objPad.DireccionTx, objPad.DireccionRx)
			else:
				# nos comunicamos por serial
				mensajeS = leerLineaSerial()
				if (mensajeS != ""):
					procesarMensajeSerial(objPad.id, mensajeS)

def escucharModulosNuevos():
	global numPadrescargados
	# buscamos nuevos elementos
	if (numPadrescargados < 2): 
		mensajeS = leerLineaSerial()
		if (mensajeS != ""):
			procesarMensajeSerial(-1, mensajeS)

		mensajeN = recivirMensajeNrf24l01(pipes[0]) # leemos por la direccion de escucha por defecto
		if (mensajeN != ""):
			procesarMensajeNrf24l01(-1, mensajeN, pipes[1], pipes[0])	# enviamos por la direccion de envio por defecto

def revisarModulos():
	global objetosPadresCargados, ultimaRevision, tiempoRespuestaObjetos

	# revisamos lo modulos cada determinados segundos
	if(millis() > ultimaRevision + 500):
		#procedemos a enviar los PING

		if(objetosPadresCargados != None):
			for objPad in objetosPadresCargados:
				enviarMensajeObjeto(objPad.id, "PING")
				# ponemos el estado del modulo en inactivo

				try:
					if (tiempoRespuestaObjetos.get(objPad.id) == None):
						desactivarObjeto(objPad.id)
					elif(ultimaRevision > int(tiempoRespuestaObjetos.get(objPad.id))  + 3000):
						desactivarObjeto(objPad.id)
				except Exception, e:
					desactivarObjeto(objPad.id)
					print("revisarModulos: Exc: {}".format(str(e)))

			ultimaRevision = millis()


#################### Funciones - proceso de mensajes entrantes ####################
def procesarMensajeNrf24l01(id, mensajeN, direcionModuloTx, direcionModuloRx):
	global tiempoRespuestaObjetos

	if(mensajeN[0:4] == "HOLA"):

		# extraemos la direccion para responder
		direcionModuloRecivida =  mensajeN[5:len(mensajeN)]
		if(str(direcionModuloTx) != direcionModuloRecivida):
			print("procesarMensajeNrf24l01: Inf: Cambiando Direccion Anterior \"{}\", por \"{}\"".format(direcionModuloTx,direcionModuloRecivida))
			direcionModuloTx = direcionModuloRecivida

		#enviamos mensaje de reconocimiento a esa direccion
		enviarMensajeNRF24L01("HOLA-IDENTIFICATE",direcionModuloTx)

	elif(mensajeN[0] == '{'): # procesamos el objeto json
		resultado = procesarJsonObjeto(id,mensajeN, direcionModuloTx, direcionModuloRx)

	elif(mensajeN == 'PONG'):

		# actualizamos el ultimo momento en que el objeto respondio al PING (solo para objetos en base de datos o con id != -1)
		if(id != -1):
			tiempoRespuestaObjetos[id] = millis()
			activarObjeto(id)

	else:
		pass

def procesarMensajeSerial(id, mensajeS):
	global tiempoRespuestaObjetos

	if(mensajeS[0:4] == "HOLA"):
		enviarMensajeSerial("HOLA-IDENTIFICATE")

	elif(mensajeS[0] == '{'):
		resultado = procesarJsonObjeto(id,mensajeS)
		
	elif(mensajeS == 'PONG'):
		# actualizamos el ultimo momento en que el objeto respondio al PING (solo para objetos en base de datos o con id != -1)
		if(id != -1):
			tiempoRespuestaObjetos[id] = millis()
			activarObjeto(id)

	else:
		pass


#################### Funciones - procedimentos mensajes ####################
def procesarJsonObjeto(id, objetoJson, direccionTx = None, direccionRx = None,):
	print("procesarJsonObjeto: Inf: Procesando Json... ")
	try:
		objetoPythonJson = json.loads(objetoJson)
		print("procesarJsonObjeto:  Ok: {}".format(objetoPythonJson))

		obj = objetoPythonJson.keys()[0] 
		val = objetoPythonJson.values()[0] 
		if(objetoExiste(obj)):
			if not isinstance(val, list):
				# revisamos que no sea un caso de cambio de estado objeto
				#mens = revisarCambioEstado(obj, val)
				#if(mens != ""):
				if(revisarCambioEstado(obj, val)):
					enviarMensajeObjeto(id,"OK-{}".format(val.keys()[0]))
					#return "estAct{}".format(mens)
			else:
				print("procesarJsonObjeto: Inf: El objeto ya se encuentra guardado")		# el objeto ya esta guardado
				enviarMensajeObjeto(id,"BIENVENIDO")

		elif(guardarObjetosJsonDB(objetoPythonJson, direccionTx, direccionRx)):
				enviarMensajeObjeto(id,"BIENVENIDO")

	except Exception, e:
		print("procesarJsonObjeto: Exc: {}".format(str(e)))
	#return ""

def revisarCambioEstado(obj, valorPythonJson):
	try:
		for variable in valorPythonJson:			# tomo al padre -> variable de estado
			val = valorPythonJson.values()[0]		# tomo el nuevo valor a cargar
			print ("revisarCambioEstado: Inf: Realizando cambio a la Variable Estado: \"{}\" del Objeto \"{}\", al Nuevo Estado: \"{}\"".format(variable,obj,val))
			if (actualizarVariableEstado(obj,variable,val)):
				print ("revisarCambioEstado: Inf: Cambio Realizado.")
				#return variable
				return True
			else:
				print ("revisarCambioEstado: Inf: Cambio Fallido.")
	except Exception, e:
		print("revisarCambioEstado: Exc: {}".format(str(e)))
	#return ""
	return False

def guardarObjetosJsonDB(objetoPythonJson, direccionTx = None, direccionRx = None, padre = "Root"):
	global objetosPadresCargados

	# tomamos el primer objeto
	for obj in objetoPythonJson:
		if(padre == "Root"):
			print("guardarObjetosJsonDB: Inf: Objeto Padre \"{}\" Reconocido".format(obj))
		else:
			print("guardarObjetosJsonDB: Inf: Objeto \"{}\" Hijo de: \"{}\" Reconocido".format(obj, padre))
		
		# verificamos que el objeto no exista ya
		if(objetoExiste(obj)):
			print("guardarObjetosJsonDB: war: Nombre Objeto \"{}\", ya Existe en la base de datos".format(obj))
			return True

		# Guardamos el objeto en la base de datos 
		guardarObjeto(obj, padre, True, str(objetoPythonJson), direccionTx, direccionRx)
		objetosPadresCargados = None # como se agrego un nuevo padre, limpio la lista de padres cargados

		idObjetoPadre = IdObjeto(obj)	# Obtenemos el Id del objeto (por su nombre) para verificar que fue creado en la base de datos
		if(idObjetoPadre == None):
			print("guardarObjetosJsonDB: Err: El Objeto \"{}\", no fue guardado correctamente, no posee id en BD".format(obj))
			return False

		# tomamos las Funciones, Estados y Objetos del primer objeto, y los procesamos 
		objetosOk = True;
		for parteObjeto in objetoPythonJson[obj]:
			for funVarObj in parteObjeto:

				if(funVarObj == "Funciones"):

					for fun in parteObjeto[funVarObj]:
						print("guardarObjetosJsonDB: Inf: Funcion \"{}\" reconocida".format(fun))
						guardarFuncion(fun, idObjetoPadre)


				elif(funVarObj == "Estados"):

					for est in parteObjeto[funVarObj]:
						print("guardarObjetosJsonDB: Inf: Variable \"{}\" reconocida".format(est))
						guardarEstado(est, idObjetoPadre)

				else:
					# agregamos esto sub-objetos de manera recursiva
					if(not guardarObjetosJsonDB(parteObjeto, None, None, obj)):
						objetosOk = False
		return objetosOk
	return False


#################### Funciones - Enviar Orden de Ejecusion ####################
def ejecutarFuncion(idObjeto,nomFun):
	nombrePadre = nombreObjeto(idObjeto)	# obtenemos el nombre del objeto enviado
	# armo el mensaje
	mensaje = {nombrePadre:nomFun}
	mensaje = str(json.dumps(mensaje,separators=(',',':')))
	print ("ejecutarFuncion: Inf: Enviando {}".format(mensaje))

	# lo envio por el medio adecuado
	enviarMensajeObjeto(idObjeto,mensaje)



################################################# Funciones - Recepcion de Informacion #################################################
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate
@static_vars(bufferRecivido="")
def leerLineaSerial():
	
	while (port.inWaiting()>0):
		ch = port.read()
		if ch == '\r' or ch =='\n':
			if(leerLineaSerial.bufferRecivido != ""):
				mensaje = leerLineaSerial.bufferRecivido
				print('Recibido Serial  : #{} {}'.format(len(mensaje), mensaje))
				leerLineaSerial.bufferRecivido = ""
				return mensaje
		if ch != '\r' and ch !='\n':
			leerLineaSerial.bufferRecivido += ch
	return ""


def recivirMensajeNrf24l01(direccionRx):
	cambiarDireccionRecepcionNrf24l01(direccionRx)
	tiempoReintentando = millis()
	mensaje = ""
	while (mensaje == "" and millis() < tiempoReintentando + 500):
		mensaje = recivirStringNrf24l01()
	return mensaje

def recivirStringNrf24l01():
	mensaje = recivirHasta32Nrf24l01()
	numeroPaquetes = 0
	# si enviaron paquetes
	if (mensaje is not None and mensaje != "" and mensaje[0] == '-'):
		numeroPaquetes = obtenerNumeroPaquetes(mensaje)		# son varios paquetes, obtengo el numero de paquetes
	# preguntamos aunque deveria ser obio
	if (numeroPaquetes > 0 ):
		mensaje = ""       # limpiamos mensaje
		contadorPaquetesRecibidos = 0
		tiempoInicioMensaje = millis()
		maximoTiempoEspera = 200     # lo que esperamos antes de cancelar el paquete
		while (contadorPaquetesRecibidos < numeroPaquetes and millis() < (tiempoInicioMensaje + maximoTiempoEspera)):
			# armamos el paquete
			paqueteLeido = recivirHasta32Nrf24l01()
			if (paqueteLeido != ""):
				mensaje += paqueteLeido
				contadorPaquetesRecibidos += 1
				# fin while varios paquetes

		# si el paquete no llego completo lo descartamos
		if (contadorPaquetesRecibidos < numeroPaquetes):
			print("Paquete Incompleto")
			return ""
		else:
			return mensaje
	# fin numero de paquetes mayor a 0
	else:
		return mensaje     #si no esta por paquetes, retornamos el mensaje recivido
  	
def recivirHasta32Nrf24l01():
	radio.startListening()
	# analizar luego del cambio
	if radio.available():
		while radio.available():
			len = radio.getDynamicPayloadSize()
			receive_payload = radio.read(len)
			dato = receive_payload.decode('utf-8')
			print('Recibido Nrf24l01: #{} {}'.format(len, dato))
			return dato
	return ""



################################################# Funciones - Envio de Informacion #################################################
def enviarMensajeObjeto(idObjeto, mensaje):
	# condicion para decididr por que medio parte el mensaje
	direcionModuloTx = direccionTxObjeto(idObjeto)

	if(direcionModuloTx != None):
		enviarMensajeNRF24L01(mensaje, direcionModuloTx)
	else:
		enviarMensajeSerial(mensaje)


#################### Funciones Envio de Mensajes ####################
def enviarMensajeNRF24L01(mensaje, direcionModuloTx):
	# nos comunicamos a travez del modulo NRF24L01
	cambiarDireccionEnvioNrf24l01(direcionModuloTx)
	tiempoReintentando = millis()
	while (not(enviarStringNrf24l01(mensaje)) and millis() < tiempoReintentando + 100):
		pass
	radio.startListening()


def enviarMensajeSerial(mensaje):
	# nos comunicamos por serial
	print("Enviando Serial  : #{} {}".format(len(mensaje),mensaje))
	port.write(mensaje)
	port.write("\n")


#################### Funciones Auxiliares Envio Mensaje NRF24L01 ####################
def enviarStringNrf24l01(mensaje):
	#convertimos el string de salida a un arreglo de caracteres usado por radio.write
	largoMensaje = len(mensaje)
	numeroPaquetes  = largoMensaje // 32
	if(largoMensaje % 32 > 0):
		numeroPaquetes += 1
	if (numeroPaquetes > 1):
		print(" Lm: {} #P: {}".format(largoMensaje,numeroPaquetes))
		# enviamos el paquete de inicio
		enviarHasta32CharNrf24l01("-" + str(numeroPaquetes) + "-")

		for i in range(numeroPaquetes):
			fin  = (i + 1) * 32
			if (fin >= largoMensaje):
				fin = largoMensaje;   # para el ultimo paquete que no es de tamaño 32*i
			paquete = mensaje[i * 32:fin]

			tiempoInicioMensaje = millis()
			maximoTiempoEspera = 100     # lo que esperamos antes de dejar de reenviar
			while (not(enviarHasta32CharNrf24l01(paquete)) and millis() < (tiempoInicioMensaje + maximoTiempoEspera)):
				pass 		# fin while reenvio
			if (not(millis() < (tiempoInicioMensaje + maximoTiempoEspera))):
				print("enviarStringNrf24l01: Err: Mensaje Cancelado, Fuera de Tiempo")
				return False   # canselamos el envio del paquete
	#fin for paquetes
	else:
		return enviarHasta32CharNrf24l01(mensaje)
	# si se logra enviar el mensaje completo
	return True

def enviarHasta32CharNrf24l01(mensaje):
	radio.stopListening()
	enviado = radio.write(mensaje)
	#radio.startListening()
	# enviamos los datos
	if(enviado):
		print("Enviando Nrf24l01: #{} {} {}".format(len(mensaje),mensaje, "Exitoso"))
	else:
		print("Enviando Nrf24l01: #{} {} {}".format(len(mensaje),mensaje," Fallido"))
	return enviado



#################### Funciones Auxiliares Comunicacion NRF24L01 ####################
def cambiarDireccionRecepcionNrf24l01(direccionRx):
	#print("cambiarDireccionRecepcionNrf24l01: tiempo in:  {}".format(millis()))
	if(direccionRx != None):
		#pass
		radio.openReadingPipe(1,int(direccionRx))
		# activar espera para recepcion
	#print("cambiarDireccionRecepcionNrf24l01: tiempo out: {}".format(millis()))

def cambiarDireccionEnvioNrf24l01(direccionTx):
	#print("cambiarDireccionEnvioNrf24l01: tiempo in {}".format(millis()))
	if(direccionTx != None):
		#pass
		radio.openWritingPipe(int(direccionTx))
	#print("cambiarDireccionEnvioNrf24l01: tiempo out {}".format(millis()))


def obtenerNumeroPaquetes(numeroPaquetes):
	numero = ""
	for i in numeroPaquetes:
		if (i != '-'):
			numero += i
	return int(numero)


################################################# Funciones - Eventos #################################################
def informarEvento(mensaje):
	socketio.emit('my response',{'data': mensaje}, namespace='/interface')
	print("Evento Ocurrido : {}".format(mensaje))


################################################# Funciones - consultas base de datos #################################################
#################### Conexion ####################
# entrega una sesison de base de datos
def createSessionDB():
	#print "Iniciando Consulta BD..."
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session
# cierra la sesison de base de datos que se entrega
def closeSessionDB(sessionDataB):
	sessionDataB.close()
	#print "Consulta BD Terminada."


#################### Guardar informacion ####################
def guardarObjeto(objeto, PadreObjeto, activo = True, jsonForm = None, direccionTx = None, direccionRx = None):
    """guarda un objeto en la base de datos"""
    DBS = createSessionDB()
    DBS.add(Objetos(NombreObjeto=objeto, NombreObjetoPadreObjeto=PadreObjeto, Activo = activo, DireccionTx=direccionTx, DireccionRx=direccionRx, FormaObjetoJson = jsonForm))
    DBS.commit()
    closeSessionDB(DBS)
    print('guardarObjeto: Inf: Objeto {} Guardado en BD.'. format(objeto))

def guardarFuncion(nombreFuncion, ObjetoPadreFuncion):
    """guarda una funcion en la base de datos"""
    DBS = createSessionDB()
    DBS.add(Funciones(NombreFuncion=nombreFuncion, NombreObjetoPadreFuncion=ObjetoPadreFuncion))
    DBS.commit()
    closeSessionDB(DBS)
    print('guardarFuncion: Inf: Funcion {} Guardada en BD.'. format(nombreFuncion))

def guardarEstado(nombreVariable, ObjetoPadreVariable, EstadoVariable =  True):
    """guarda una variable de estado en la base de datos"""
    DBS = createSessionDB()
    DBS.add(Variables(NombreVariable=nombreVariable, NombreObjetoPadreVariable=ObjetoPadreVariable, EstadoVariable = EstadoVariable))
    DBS.commit()
    closeSessionDB(DBS)
    print('guardarEstado: Inf: Estado: {} Guardado en BD.'. format(nombreVariable))


#################### Colsuta de Informacion ####################
def cargarObjetosPadres():
	DBS = createSessionDB()
	try:
		objetos = DBS.query(Objetos).filter_by(NombreObjetoPadreObjeto="Root").all()
		if(objetos != None):
			return objetos
		else:
			print("cargarObjetosPadres: Inf: No hay objetos en la base de datos")
	except Exception, e:
		print("cargarObjetosPadres: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return None

def objetoExiste(Nombreobjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(NombreObjeto=Nombreobjeto).first()
		if(objetoleido != None):
			if(objetoleido.NombreObjeto == Nombreobjeto):
				return True
		else:
			print("objetoExiste: Inf: El objeto \"{}\" no existe en la base de datos". format(Nombreobjeto))
	except Exception, e:
		print("objetoExiste: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return False


#################### Obtener Valores Objetos ####################
def IdObjeto(NombreObjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(NombreObjeto=NombreObjeto).first()
		if(objetoleido.id != None):
			return objetoleido.id
	except Exception, e:
		print("IdObjeto: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return None

def nombreObjeto(idObjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(id=idObjeto).first()
		if(objetoleido != None):
			return objetoleido.NombreObjeto
		else:
			print("nombreObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos". format(idObjeto))
	except Exception, e:
		print("nombreObjeto: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return None

def direccionTxObjeto(idObjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(id=idObjeto).first()
		if(objetoleido != None):
			return objetoleido.DireccionTx
		else:
			print("direccionTxObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos". format(idObjeto))
	except Exception, e:
		print("direccionTxObjeto: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return None

def direccionRxObjeto(idObjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(id=idObjeto).first()
		if(objetoleido != None):
			return objetoleido.DireccionRx
		else:
			print("direccionRxObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos". format(idObjeto))
	except Exception, e:
		print("direccionRxObjeto: Exc: {}".format(str(e)))
	closeSessionDB(DBS)
	return None

def obtenerPadreObjeto(idObjeto):
	DBS = createSessionDB()
	objetoleido = None
	try:
		objetoleido = DBS.query(Objetos).filter_by(id=idObjeto).first()
		if(objetoleido != None):
			return objetoleido.NombreObjetoPadreObjeto
		else:
			print("obtenerPadreObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos". format(idObjeto))
	except Exception, e:
		print("Exception obtenerPadreObjeto: {}".format(str(e)))
	closeSessionDB(DBS)
	return None


#################### Cambio Estado Activacion ####################
def desactivarObjeto(id):
	try:
		DBS = createSessionDB()
		objetoleido = DBS.query(Objetos).filter_by(id=id).first()
		if(objetoleido != None):
			if (objetoleido.Activo != False):
				objetoleido.Activo = False
				DBS.commit()
				informarEvento("Objeto \"{}\" Desactivado".format(objetoleido.NombreObjeto))
		else:
			print("desactivarObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos".format(id))
		closeSessionDB(DBS)
	except Exception, e:
		print("desactivarObjeto: Exc: {}".format(str(e)))
		return False
	return True

def activarObjeto(id):
	try:
		DBS = createSessionDB()
		objetoleido = DBS.query(Objetos).filter_by(id=id).first()
		if(objetoleido != None):
			if (objetoleido.Activo != True):
				objetoleido.Activo = True
				DBS.commit()
				informarEvento("Objeto \"{}\" Activado".format(objetoleido.NombreObjeto))
		else:
			print("activarObjeto: Inf: El idObjeto \"{}\" no existe en la base de datos".format(id))
		closeSessionDB(DBS)
	except Exception, e:
		print("activarObjeto: Exc: {}".format(str(e)))
		return False
	return True

def actualizarVariableEstado(nombreObjetoPadre,nomVariable,nuevoEstadoVariable):
	"""editamos el estado de una variable de estado"""
	if (nuevoEstadoVariable == "1"):
		nEstadoVariable = True
	else:
		nEstadoVariable = False
	try:
		DBS = createSessionDB()
		objetoleido = DBS.query(Objetos).filter_by(NombreObjeto=nombreObjetoPadre).first()
		variable = DBS.query(Variables).filter_by(NombreVariable=nomVariable, NombreObjetoPadreVariable= objetoleido.id).first()
		if(variable.EstadoVariable != nEstadoVariable):
			print("actualizarVariableEstado: Inf: Cambiando la variable \"{}\" del Objeto  \"{}\", del estado \"{}\" al estado \"{}\"".format(str(variable.NombreVariable),str(objetoleido.NombreObjeto),str(variable.EstadoVariable),str(nEstadoVariable)))
			variable.EstadoVariable = nEstadoVariable
			DBS.commit()
			informarEvento("El {}, Cambio.".format(nomVariable))
		
		closeSessionDB(DBS)
	except Exception, e:
		print("actualizarVariableEstado: Exc: {}".format(str(e)))
		return False
	return True


#################### Borrar informacion ####################
def borrarObjetos(DB,objetos):
    for obj in objetos:
        DB.delete(obj)
    DB.commit()


#################### Visualizar Informacion ####################
# muestra la lista de objetos que se pasa
def mostrarObjetos(objetos):
    for obj in objetos:
        #print obj
        print("{} , {} , {} , {} , {} , {}, {}".format(obj.id, obj.NombreObjeto, obj.NombreObjetoPadreObjeto,obj.Activo,obj.FormaObjetoJson,obj.DireccionTx,obj.DireccionRx))

