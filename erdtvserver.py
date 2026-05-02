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
import hashlib
import json
import math
import os
import random
import struct
import sys
from pathlib import Path
app = Flask(__name__)

# Importando datos del juego y otras cosas
from erdtv_data import *

# Vamos a hacer todo el trabajo con los archivos de una sola vez
#
# Declaramos los diccionarios necesarios
dictCancionesListas = {}
dictCancionesAutorizadas = {}

# CONCEPTO:
#    El juego tiene los metadatos de sus canciones en los archivos CBR,
#    entonces, nosotros vamos a generar una lista dinámica directamente
#    usando la metadata disponible.
#    También, vamos a generar el auth desde acá así el juego tiene
#    todo lo necesario para validar toda la info.
#    Esto puede hacer andar DLCs futuros, así como... ¿customs?
#    (giga copium)
#    AVISO: CONTIENE CÓDIGO GENERADO CON IA
#
# 
def getAllSongsData():
    # Primero, vamos a establecer los datos necesarios para este proceso
    # siendo contadores, paths, etc.
    dirCanciones=os.getenv('TES_DIR_JUEGO', os.path.dirname(sys.executable))
    pathCancionesInstaladas = os.path.join(dirCanciones, 'data', 'mozart', 'song')
    # Prefijo necesario para validar los hashes de authorizedsongs
    prefijoValidador = bytes.fromhex('b52167b41e4589fec5aa94')
    print("Generando las listas de canciones...")


    # Arrancando los elementos necesarios para la lista final
    countCancionesAutorizadas = 0
    countCancionesDisponibles = 0
    existeCarpetaCBR = False

    # Buscar si hay canciones en el directorio
    if os.path.exists(dirCanciones):
        existeCarpetaCBR = True
        listaCancionesCBR = list(Path(pathCancionesInstaladas).glob("*.cbr"))
        if listaCancionesCBR:
            for archivoChart in listaCancionesCBR:
                # Metadatos de la cancion a analizar
                songidArchivo = archivoChart.stem  # nombre sin extensión
                pathArchivo = str(archivoChart)

                # Leemos el archivo cbr
                with open(pathArchivo, 'rb') as f:
                    # Necesario para el hash de la cancion
                    contenidoCBR = f.read()

                    # Necesario para los metadatos de la cancion
                    # Leer campos de tamaño fijo (no se usa por que sacamos el songid del nombre del archivo)
                    #f.seek(0x0B)                   # offset de songid,
                    #songidExtraida = struct.unpack('<Q', f.read(8))[0]   # 8 bytes, little-endian
                    f.seek(0x1C)
                    bandaExtraida = struct.unpack('<Q', f.read(8))[0]
                    f.seek(0x23)
                    discoExtraido = struct.unpack('<Q', f.read(8))[0]
                    f.seek(0x2C)
                    anioExtraido = struct.unpack('<H', f.read(2))[0]     # 2 bytes, little-endian

                    # Leer título (UTF-16LE hasta doble nulo)
                    f.seek(0x30)
                    titulo_bytes = []
                    while True:
                        b = f.read(2)
                        if b == b'\x00\x00':
                            break
                        titulo_bytes.append(b)
                    tituloExtraido = b''.join(titulo_bytes).decode('utf-16-le')

                    # Posición después del doble nulo
                    pos_despues_titulo = f.tell()   # apunta justo después de los dos bytes nulos
                    # Saltar 10 bytes (offset fijo según análisis)
                    f.seek(pos_despues_titulo + 10)
                    # Leer 4 bytes de dificultades (guitarra, bajo, batería, voz)
                    difGuitarraExtraida, difBajoExtraida, difBateriaExtraida, difVozExtraida = struct.unpack('4B', f.read(4))

                    # Dificultad general = promedio redondeado para abajo
                    difGralCalculada = math.floor((difGuitarraExtraida + difBajoExtraida + difBateriaExtraida + difVozExtraida) / 4)

                # Hashear y guardar cancion autorizada
                md5Cancion = hashlib.md5(prefijoValidador + contenidoCBR).hexdigest()
                nuevaCancionAutorizada = {
                     'songid': songidArchivo, 
                     'hash': [str(md5Cancion)]
                }
                nuevaCancionAuth = {str(countCancionesAutorizadas): nuevaCancionAutorizada}
                dictCancionesAutorizadas.update(nuevaCancionAuth)
                countCancionesAutorizadas += 1

                # Guardar la cancion disponible con sus metadatos
                nuevaCancionLista = {
                     'songid': songidArchivo, 
                     'banda': bandaExtraida, 
                     'cancion': tituloExtraido, 
                     'disco': discoExtraido, 
                     'anio': str(anioExtraido), 
                     'dif_gral': str(difGralCalculada), 
                     'dif_guitarra': str(difGuitarraExtraida), 
                     'dif_bajo': str(difBajoExtraida), 
                     'dif_bateria': str(difBateriaExtraida), 
                     'dif_voz': str(difVozExtraida)
                }
                nuevaCancionDisp = {str(countCancionesDisponibles): nuevaCancionLista}
                dictCancionesListas.update(nuevaCancionDisp)
                countCancionesDisponibles += 1
        else:
            print("No se encontraron archivos .cbr en " + pathCancionesInstaladas + ". El juego crashea si no tiene canciones.")
            existeCarpetaCBR = False
    else:
        print("Hubo un error al encontrar el directorio de las canciones. Se buscó en:" + pathCancionesInstaladas)
    if not existeCarpetaCBR:
        # En caso de que falle, solo usar la info de envido32 para canciones disponibles
        for cancionDisp in listaCanciones:
            # Añadiendo metadatos irrelevantes
            cancionDisp.update(datosExtraCanciones)

            # Añadiendo esto como un item nuevo
            nuevaCancion = {str(countCancionesDisponibles): cancionDisp}
            dictCancionesListas.update(nuevaCancion)
            countCancionesDisponibles += 1
    print("Se autorizaron " + str(countCancionesAutorizadas) + " canciones y se encuentran " + str(countCancionesDisponibles) + " canciones para jugar.") 

# Página de prueba
@app.route('/')
@app.route('/index')
def index():
    return 'Si estás viendo esto, que vuelva bootleggers. #AndroidCustomROMs'


@app.route('/game/rest.php', methods=['POST'])
def game_rest():
    # Inicializando las listas de canciones solo si no tenemos datos
    if not dictCancionesAutorizadas or not dictCancionesListas:
        getAllSongsData()

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
    if tipoRequest=="login": 
        tipoContent = { 
            'userid': '000001',
            'sessionid': '1', 
            'nick': datosRequest['username'] 
        }

    elif tipoRequest=="logout":
        tipoContent = {
            'userid': '000001',
            'sessionid': '0'
        }

    elif tipoRequest=="getticker":
        strTicker = listaTicker[random.randrange(1, len(listaTicker))]
        if strTicker != "bolas":
            strTicker = strTicker.upper()

        tipoContent = {
            'ticker': [strTicker]
        }

    elif tipoRequest=="getallsongs":
        tipoContent = {
            'songs': dictCancionesListas,
            'table': ""
        }

    elif tipoRequest=="getauthorizedsongs":
        tipoContent = {
        'songs': dictCancionesAutorizadas
        }

    elif tipoRequest=="submithighscore":
        # TODO: Generacion de hash propiamente hecha - ALGORITMO TEMPORAL HECHO CON IA
        # Generación de los hashes, PENDIENTE VER QUE PASA EN ESTA REQ
        #saltPuntajes = bytes.fromhex("B52167B41E4589FEC5AA94")
        #payload = str("08CD95C9").encode('ascii') + str(2011).encode('ascii') + saltPuntajes
        md5_handler = hashlib.md5()
        md5_handler.update(str(requestData))

        tipoContent = {
            'hash': str(md5_handler.hexdigest().upper())
        }

    elif tipoRequest=="gethighscorepos":
        tipoContent = {
            'songid': datosRequest['songid'],
            'instrumentid': datosRequest['instrumentid'],
            'level': datosRequest['level'],
            'score': '0',
            'gamemode': datosRequest['gamemode']
        }

    elif tipoRequest=="gethighscore":
        tipoContent = {
            'songid': datosRequest['songid'],
            'instrumentid': datosRequest['instrumentid'],
            'level': datosRequest['level'],
            'gamemode': datosRequest['gamemode'],
            'startpos': '0',
            'count': '0',
            'userid': '000001'
        }

    elif tipoRequest=="getads":
        tipoContent = {
            'userid': '000001',
            'sessionid': requestData['sessionid']
        }

    elif tipoRequest=="extra":
        tipoContent = {}

    else:
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
