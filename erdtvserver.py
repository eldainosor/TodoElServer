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
import hashlib
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

        case 'logout':
            tipoContent = {
                'userid': '000001',
                'sessionid': '0'
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

        case 'submithighscore':
            # TODO: Generacion de hash propiamente hecha - ALGORITMO TEMPORAL HECHO CON GEMINI
            # Generación de los hashes, PENDIENTE VER QUE PASA EN ESTA REQ
            #saltPuntajes = bytes.fromhex("B52167B41E4589FEC5AA94")
            #payload = str("08CD95C9").encode('ascii') + str(2011).encode('ascii') + saltPuntajes
            md5_handler = hashlib.md5()
            md5_handler.update(str(requestData))
            tipoContent = {
                'hash': str(md5_handler.hexdigest().upper())
            }

        case 'gethighscorepos':
            tipoContent = {
                'songid': datosRequest['songid'],
                'instrumentid': datosRequest['instrumentid'],
                'level': datosRequest['level'],
                'score': '0',
                'gamemode': datosRequest['gamemode']
            }

        case 'gethighscore':
            tipoContent = {
                'songid': datosRequest['songid'],
                'instrumentid': datosRequest['instrumentid'],
                'level': datosRequest['level'],
                'gamemode': datosRequest['gamemode'],
                'startpos': '0',
                'count': '0',
                'userid': '000001'
            }

        case 'getads':
            tipoContent = {
                'userid': '000001',
                'sessionid': datosRequest['sessionid']
            }

        case 'extra':
            tipoContent = {}

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
