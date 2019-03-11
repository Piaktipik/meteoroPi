# import the Flask class from the flask module

# creacion de thread
import thread
# importamos archivos auxiliares propios
from interfaceFun import *
# otras
import datetime

# detectamos el cierre de la aplicacion para cerrarla correctamente
import signal
import sys
# funcion que es ejecutada cuando finaliza la aplicacion
def signal_handler(signal, frame):
        print('')       # linea en blanco
        print('Cerrando...')
        #GPIO.output(puertoArduinoEscucha, False)
        #GPIO.cleanup()  # ponemos lo puertos digitales como entrada para proteger la raspberry
        #thread.exit()
        print('Aplicacion Cerrada, Adios.')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# use decorators to link the function to a url
@app.route('/')
def show_obj():
    '''procesmo a listar los objetos activos'''
    objetos = g.db.query(Objetos).filter_by(NombreObjetoPadreObjeto="Root").filter_by(Activo=True).all()
    #mostrarObjetos(objetos)
    return render_template('show_objects.html',padre="Objetos Activos", objetos=objetos)


@app.route('/obj_info')
def get_obj():
    """obteniene los elementos de un objeto padre"""
    idPadre = request.args.get('id')
    nombrePadre = nombreObjeto(idPadre)
    global variablesActualizables
    variablesActualizables = -1
    print("consulta objetos id: {}, padre: {}".format(idPadre,nombrePadre))

    try:
        objetos = g.db.query(Objetos).filter_by(NombreObjetoPadreObjeto=nombrePadre).filter_by(Activo=True).all()
    except NoResultFound:
        print "NO resultados para el padre {}".format(nombrePadre)
        objetos = []

    try:
        funciones = g.db.query(Funciones).filter_by(NombreObjetoPadreFuncion=idPadre).all()
    except NoResultFound:
        print "NO funciones para el padre {}".format(nombrePadre)
        funciones = []

    try:
        variables = g.db.query(Variables).filter_by(NombreObjetoPadreVariable=idPadre).all()
    except NoResultFound:
        print "NO variables para el padre {}".format(nombrePadre)
        variables = []
    if nombrePadre != None:
        Padre="Elementos de {}".format(nombrePadre)
    else:
        Padre="Objetos Activos"
    return render_template('show_objects.html',padre=Padre, objetos=objetos, funciones=funciones, variables=variables)


@app.route('/search', methods=['POST'])
def search_db():
    """Used to search for a referee in the database"""
    print "asdfasdfsda"
    """
    term = request.form["term"]
    q1 = g.db.query(Referee).filter(Referee.f_name.like('%{0}%'.format(term)))
    q2 = g.db.query(Referee).filter(Referee.l_name.like('%{0}%'.format(term)))

    results = q1.union(q2).all()
    return render_template('search_results.html', results=results)
    """

@app.before_request
def before_request():
    print "Iniciando Consulta BD..."
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    g.db = session

@app.teardown_appcontext
def close_db(error):
    print "Consulta BD Terminada."
    if hasattr(g, 'sqlite_db'):
        g.db.close()

# funcion de comunicaciones
def flaskThread():
    while(1):
        Interface()

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key interface'     # usado para la criptografia de las cookies
))

# start the server with the 'run()' method
if __name__ == '__main__':
    # inciamos un hilo para el manejo de las comunicaciones seriales y de los modulos NRF24L01 con los modulos
    thread.start_new_thread(flaskThread,())
    print('Iniciando App')
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False)#app.run(host='0.0.0.0', port=8080, debug=True, threaded=True, use_reloader=False)
