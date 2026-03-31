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
import os
from pathlib import Path
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
            # Concepto: Buscar dinámicamente que canciones tiene
            #           el usuario instaladas en el juego y generamos
            #           una lista de canciones válidas para usar.
            #           Se podrían agregar las 28 canciones disponibles
            #           a la hora de redactar esto, pero no se como se comporta
            #           cuando alguna de esas no estén instaladas.
            #           De paso, lo hacemos que funcione a futuro
            #           en caso que aparezca más DLC (copium)
            #
            # CONTIENE CÓDIGO GENERADO CON IA
            #
            # Vamos a establecer lo básico antes de empezar, el prefijo válido
            prefijoValidador = bytes.fromhex('b52167b41e4589fec5aa94')
            # Establecemos el directorio actual donde estarían los charts
            dirCanciones=os.path.dirname(sys.executable)
            pathCancionesInstaladas = os.path.join(dirCanciones, 'data', 'mozart', 'song')
            # Arrancando los elementos necesarios para la lista final
            authItemCount = 0
            dictCancionesAutorizadas = {}

            # Buscar las canciones en el directorio
            if os.path.exists(dirCanciones):
                listaCancionesCBR = list(Path(pathCancionesInstaladas).glob("*.cbr"))
                if listaCancionesCBR:
                    for archivoChart in listaCancionesCBR:
                        songidArchivo = archivoChart.stem  # nombre sin extensión
                        pathArchivo = str(archivoChart)

                        # Leemos el archivo cbr
                        with open(pathArchivo, 'rb') as f:
                            contenido = f.read()
                        md5Cancion = hashlib.md5(prefijoValidador + contenido).hexdigest()

                        nuevaCancionAutorizada = {
                             'songid': songidArchivo, 
                             'hash': [str(md5Cancion)]
                        }

                        # Añadiendo esto como un item nuevo
                        nuevaCancion = {str(authItemCount): nuevaCancionAutorizada}
                        dictCancionesAutorizadas.update(nuevaCancion)
                        authItemCount += 1
                else:
                    print("No se encontraron archivos .cbr en " + pathCancionesInstaladas + ". El juego crashea si no tiene canciones.")
            else:
                print("Hubo un error al encontrar el directorio de las canciones. Se buscó en:" + pathCancionesInstaladas)
            tipoContent = {
                'songs': dictCancionesAutorizadas
            }

        case 'submithighscore':
            # TODO: Generacion de hash propiamente hecha - ALGORITMO TEMPORAL HECHO CON IA
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
                'sessionid': requestData['sessionid']
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

    respuestaFinal = json.dumps(respuestaFormateada, indent=4, ensure_ascii=False).encode('cp1252')
    print("Respuesta generada:")
    print(respuestaFinal)

    return respuestaFinal

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4637, debug=False)
