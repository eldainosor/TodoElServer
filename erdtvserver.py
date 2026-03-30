# Todo el Server, un servidor recreado para El Rock De Tu Vida.
# Autor: ElDainosor, 2025/2026.
# Objetivo: Recrear con flask un servidor ejecutable
#           que permita acceder a cualquier usuario
#           a jugar a El Rock de Tu Vida con un parche
#           y 2 pancitos, sin hosts, ni XAMPP. 
#           
#           Solo va a necesidar un parche en el juego
#           para redireccionar llamados:
#           www.elrockdetuvida.com --> localhost:4637
#                                      (nuevo server fantasma)

# Inicializando Flask
from flask import Flask, request
import random
app = Flask(__name__)

# Importando datos del juego y otras cosas
from erdtv_data import *

# Página de prueba
@app.route('/')
@app.route('/index')
def index():
    return 'Si estás viendo esto, que vuelva bootleggers. #AndroidCustomROMs'


@app.route('/game/rest.php', methods=['POST'])
def game_rest():
    # Prueba de ERDTV
    #print("Tipo de peticion:" + requestData['type'])
    #print(str(requestData['content']))

    # Extraer las peticiones del juego.
    requestData = eval(request.form.get('packet'))
    print(request.form.get('packet'))

    # Extraer información importante
    tipoRequest = requestData['type']
    try:
        datosRequest = requestData['content']
    except:
        datosRequest = {}

    match tipoRequest:
        case 'login':
            print('{"result": "success", "content": {"userid":"000001", "sessionid": "1", "nick": "' + datosRequest['username'] + '"}}')
            return '{"result": "success", "content": {"userid":"000001", "sessionid": "1", "nick": "' + datosRequest['username'] + '"}}'

        case 'getticker':
            strTicker = listaTicker[random.randrange(1, len(listaTicker))]
            if strTicker != "bolas":
                strTicker = strTicker.upper()
            return '{"result":"success", "content": {"ticker":["' + strTicker'"]}}'

        case _:
            return '{"result":"other"}'

    # Loop through list of dictionaries
    for cancionDisponible in listaCanciones:
        print(f"{cancionDisponible['cancion']} cantada por {cancionDisponible['banda']} tiene el id {cancionDisponible['disco']}.")
    return '{}'