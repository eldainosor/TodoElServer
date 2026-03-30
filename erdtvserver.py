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
import json
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
    print("Consulta del juego:")
    print(request.form.get('packet'))

    # Extraer información importante
    tipoRequest = requestData['type']
    try:
        datosRequest = requestData['content']
    except:
        datosRequest = {}

    # Tipos de respuesta
    resultNormal = "success"
    resultFallback = "other"

    # Generalmente las respuestas que vamos a tener son exitosas... excepto en las que no conozcamos.
    tipoResult = resultNormal

    # Escribiendo respuestas según la ocasión
    match tipoRequest:
        case 'login':
            tipoContent = {
                'userid': '000001',
                'sessionid': '1',
                'nick': datosRequest['username']
            }

        case 'getticker':
            strTicker = listaTicker[random.randrange(1, len(listaTicker))]
            if strTicker != "bolas":
                strTicker = strTicker.upper()

            tipoContent = {
                'ticker': [strTicker]
            }

        case 'getallsongs':
            itemCount = 0
            dictCanciones = {}
            for cancion in listaCanciones:
                # Añadiendo metadatos irrelevantes
                cancion.update(datosExtraCanciones)

                # Añadiendo esto como un item nuevo
                nuevaCancion = {str(itemCount): cancion}
                dictCanciones.update(nuevaCancion)
                itemCount += 1

            tipoContent = {
                'songs': dictCanciones,
                'table': ""
            }

        case 'getauthorizedsongs':
            authItemCount = 0
            dictCancionesAutorizadas = {}
            for cancion in listaCancionesAutorizadas:
                # Añadiendo metadatos irrelevantes
                cancion.update(datosExtraCanciones)

                # Añadiendo esto como un item nuevo
                nuevaCancion = {str(authItemCount): cancion}
                dictCancionesAutorizadas.update(nuevaCancion)
                authItemCount += 1

            tipoContent = {
                'songs': dictCancionesAutorizadas
            }

        case _:
            tipoResult = resultFallback
            tipoContent = {}

    respuestaFormateada = {
        'result': tipoResult,
        'content': tipoContent
    }
    print("Respuesta generada:")
    print(json.dumps(respuestaFormateada, indent=4))

    return json.dumps(respuestaFormateada, indent=4)
