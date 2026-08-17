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
from flask import Flask, request, send_file, abort, redirect, url_for, send_from_directory
import hashlib
import json
import math
import os
import random
import struct
import sys
from pathlib import Path

# Importando datos del juego y otras cosas
from erdtv_data import *

# Necesario para exportar cosas estáticas
def get_bundle_dir():
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

# Declaración inicial de la app
app = Flask(__name__,
            static_url_path='/static',
            static_folder=os.path.join(get_bundle_dir(), 'static'))

# Vamos a hacer todo el trabajo con los archivos de una sola vez
#
# Declaramos los diccionarios necesarios
dictCancionesCatalogo = {}
dictCancionesAutorizadas = {}
listAdsFinal = {}

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
def indexarCatalogo(basePath):
    # Devuelve un dict {songid: entrada_json} a partir de basePath/catalog.json.
    # Si no existe la carpeta o el catalog.json, devuelve {} (queda como fallback).
    resultado = {}
    catalogPath = Path(basePath) / "catalog.json"
    if not Path(basePath).exists() or not catalogPath.exists():
        return resultado

    with open(catalogPath, 'r', encoding='utf-8') as f:
        catalogo = json.load(f)  # lista de objetos

    for entrada in catalogo:
        resultado[entrada['songid']] = entrada
    return resultado

def resolverAssets(songid, entradaCatalogo, nombreOrigen, pathOrigen):
    # Valores base (fallback)
    cancion_tapa_file = "/static/assets/preview/0" + songid + ".cover"
    cancion_tapa_hash = "5dfc4a1d4666de864f05e14cb2665e02"
    cancion_prev_file = "/static/assets/preview/0" + songid + ".prev"
    cancion_prev_hash = "9bbd8bf5beb3b8cd94c8b666aa6b1580"
    urlCancion = request.host_url + "website/index.php"

    # Los .png/.wav viven en subcarpetas cover/ y prev/ dentro de official/customs
    pngPath = Path(pathOrigen) / "cover" / f"0{songid}.png"
    wavPath = Path(pathOrigen) / "prev" / f"0{songid}.wav"

    if pngPath.exists():
        cancion_tapa_file = f"/static/assets/preview/{nombreOrigen}/cover/0{songid}.png"
        with open(pngPath, 'rb') as f:
            cancion_tapa_hash = hashlib.md5(f.read()).hexdigest()
    # si el .png no existe, se queda con el fallback ya seteado arriba

    if wavPath.exists():
        cancion_prev_file = f"/static/assets/preview/{nombreOrigen}/prev/0{songid}.wav"
        with open(wavPath, 'rb') as f:
            cancion_prev_hash = hashlib.md5(f.read()).hexdigest()
    # si el .wav no existe, se queda con el fallback ya seteado arriba

    if entradaCatalogo.get('url'):
        urlCancion = entradaCatalogo['url']

    return cancion_tapa_file, cancion_tapa_hash, cancion_prev_file, cancion_prev_hash, urlCancion

def getAllSongsData():
    # Primero, vamos a establecer los datos necesarios para este proceso
    # siendo contadores, paths, etc.
    dirCanciones=os.getenv('TES_DIR_JUEGO', os.path.dirname(sys.executable))
    pathBandasInstaladas = os.path.join(dirCanciones, 'data', 'mozart', 'band')
    pathDiscosInstaladas = os.path.join(dirCanciones, 'data', 'mozart', 'disc')
    pathCancionesInstaladas = os.path.join(dirCanciones, 'data', 'mozart', 'song')
    # Prefijo necesario para validar los hashes de authorizedsongs
    prefijoValidador = bytes.fromhex('b52167b41e4589fec5aa94')
    print("Generando las listas de canciones...")

    # Indexamos los catálogos de official y customs (si existen), por songid.
    # Jerarquía de prioridad: customs > official > fallback hardcodeado.
    pathOfficial = os.path.join(get_bundle_dir(), "static/assets/preview/official")
    pathCustoms  = os.path.join(get_bundle_dir(), "static/assets/preview/customs")
    catalogoOfficial = indexarCatalogo(pathOfficial)
    catalogoCustoms  = indexarCatalogo(pathCustoms)

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
                    f.seek(0x24)
                    discoExtraido = struct.unpack('<Q', f.read(8))[0]
                    f.seek(0x2C)
                    anioExtraido = struct.unpack('<I', f.read(4))[0]     # 4 bytes, little-endian

                    # Leer título (UTF-16LE hasta doble nulo)
                    f.seek(0x30)
                    titulo_bytes = []
                    while True:
                        b = f.read(2)
                        if b == b'\x00\x00':
                            break
                        titulo_bytes.append(b)
                    tituloExtraido = b''.join(titulo_bytes).decode('utf-16-le')

                    # Buscamos el punto en donde estan los metadatos de dificultad directamente
                    f.seek(0x160)
                    # Leer 4 bytes de dificultades (guitarra, bajo, batería, voz)
                    difGuitarraExtraida, difBajoExtraida, difBateriaExtraida, difVozExtraida = struct.unpack('<HHHH', f.read(8))

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

                archivoBanda = Path(pathBandasInstaladas) / f"{format(bandaExtraida, 'X')}.band"
                if archivoBanda:
                    with open(str(archivoBanda), "rb") as f:
                        f.seek(4)  # skip magic
                        f.read(4)  # version
                        band_id = struct.unpack('<Q', f.read(8))[0]
                        band_name_raw = f.read(0x7F0)
                        band_name_extraido = band_name_raw.decode('utf-16-le').rstrip('\x00')

                archivoDisco = Path(pathDiscosInstaladas) / f"{format(discoExtraido, 'X')}.disc"
                if archivoDisco:
                    with open(str(archivoDisco), "rb") as f:
                        f.seek(4)  # skip magic
                        f.read(4)  # version
                        disc_id = struct.unpack('<Q', f.read(8))[0]
                        f.read(8)  # band_id
                        disc_name_raw = f.read(0x100)
                        disc_name_extraido = disc_name_raw.decode('utf-16-le').rstrip('\x00')

                # Valores base (fallback)
                cancion_tapa_file = "/static/assets/preview/0" + songidArchivo + ".cover"
                cancion_tapa_hash = "5dfc4a1d4666de864f05e14cb2665e02"
                cancion_prev_file = "/static/assets/preview/0" + songidArchivo + ".prev"
                cancion_prev_hash = "9bbd8bf5beb3b8cd94c8b666aa6b1580"
                urlCancion = request.host_url + "website/index.php"
                flagCancionNueva = "no"

                # Jerarquía: customs > official > fallback
                if songidArchivo in catalogoCustoms:
                    cancion_tapa_file, cancion_tapa_hash, cancion_prev_file, cancion_prev_hash, urlCancion = \
                        resolverAssets(songidArchivo, catalogoCustoms[songidArchivo], "customs", pathCustoms)
                    flagCancionNueva = "si"
                elif songidArchivo in catalogoOfficial:
                    cancion_tapa_file, cancion_tapa_hash, cancion_prev_file, cancion_prev_hash, urlCancion = \
                        resolverAssets(songidArchivo, catalogoOfficial[songidArchivo], "official", pathOfficial)
                    flagCancionNueva = "no"

                # Guardar la cancion disponible con sus metadatos
                nuevaCancionCatalogo = {
                     'songid': songidArchivo,
                     'banda': band_name_extraido,
                     'cancion': tituloExtraido.upper(),
                     'disco': disc_name_extraido,
                     'anio': str(anioExtraido),
                     'dif_gral': str(difGralCalculada),
                     'dif_guitarra': str(difGuitarraExtraida),
                     'dif_bajo': str(difBajoExtraida),
                     'dif_bateria': str(difBateriaExtraida),
                     'dif_voz': str(difVozExtraida),
                     'nueva': flagCancionNueva,
                     'tapa_server': 'localhost',
                     'tapa_path': cancion_tapa_file,
                     'tapa_hash': cancion_tapa_hash,
                     'preview_server': 'localhost',
                     'preview_path': cancion_prev_file,
                     'preview_hash': cancion_prev_hash,
                     'url': urlCancion
                }
                nuevaCancionDisp = {str(countCancionesDisponibles): nuevaCancionCatalogo}
                dictCancionesCatalogo.update(nuevaCancionDisp)
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
            dictCancionesCatalogo.update(nuevaCancion)
            countCancionesDisponibles += 1

    # Extender el catálogo con canciones de official/customs que todavía no
    # tengan un .cbr instalado (por ejemplo, customs recién publicadas y aún
    # no descargadas por el usuario). Se muestran en getallsongs con su url
    # de descarga, pero no se autorizan para jugar hasta tener el .cbr real.
    songidsExistentes = {v['songid'] for v in dictCancionesCatalogo.values()}

    catalogoExtendido = {}
    catalogoExtendido.update(catalogoOfficial)  # menor prioridad
    catalogoExtendido.update(catalogoCustoms)   # mayor prioridad, pisa si coincide

    for songidCatalogo, entradaCatalogo in catalogoExtendido.items():
        if songidCatalogo in songidsExistentes:
            continue  # ya está cubierto por un .cbr, no duplicar

        nombreOrigen = "customs" if songidCatalogo in catalogoCustoms else "official"
        pathOrigen = pathCustoms if nombreOrigen == "customs" else pathOfficial

        cancion_tapa_file, cancion_tapa_hash, cancion_prev_file, cancion_prev_hash, urlCancion = \
            resolverAssets(songidCatalogo, entradaCatalogo, nombreOrigen, pathOrigen)

        nuevaCancionCatalogo = {
             'songid': songidCatalogo,
             'banda': entradaCatalogo.get('banda', ''),
             'cancion': entradaCatalogo.get('cancion', '').upper(),
             'disco': entradaCatalogo.get('disco', ''),
             'anio': str(entradaCatalogo.get('anio', '')),
             'dif_gral': str(entradaCatalogo.get('dif_gral', '0')),
             'dif_guitarra': str(entradaCatalogo.get('dif_guitarra', '0')),
             'dif_bajo': str(entradaCatalogo.get('dif_bajo', '0')),
             'dif_bateria': str(entradaCatalogo.get('dif_bateria', '0')),
             'dif_voz': str(entradaCatalogo.get('dif_voz', '0')),
             'nueva': "si" if nombreOrigen == "customs" else "no",
             'tapa_server': 'localhost',
             'tapa_path': cancion_tapa_file,
             'tapa_hash': cancion_tapa_hash,
             'preview_server': 'localhost',
             'preview_path': cancion_prev_file,
             'preview_hash': cancion_prev_hash,
             'url': urlCancion
        }
        nuevaCancionDisp = {str(countCancionesDisponibles): nuevaCancionCatalogo}
        dictCancionesCatalogo.update(nuevaCancionDisp)
        countCancionesDisponibles += 1

    print("Se autorizaron " + str(countCancionesAutorizadas) + " canciones y se encuentran " + str(countCancionesDisponibles) + " canciones para jugar.")

# Página de prueba
@app.route('/')
def redir():
    return redirect('/website/index.php')

@app.route('/website/index.php')
def index():
    try:
        # Ensure the file exists before serving
        file_path = os.path.join(app.static_folder, 'erdtv.html')
        if not os.path.isfile(file_path):
            abort(404, description="Static HTML file not found.")
        return send_from_directory(app.static_folder, 'erdtv.html')
    except Exception as e:
        return f"Error serving file: {e}", 500

@app.route('/static/assets/preview/<path:filename>')
def serve_placeholder(filename):
    print("Abriendo el filename " + filename)
    if filename.endswith('.cover'):
        path = 'static/assets/preview/placeholder_cover.png'
    elif filename.endswith('.prev'):
        path = 'static/assets/preview/placeholder_preview.wav'
    else:
        # filename ya viene con el subpath incluido (official/0XXXX.png o customs/0XXXX.png)
        if Path('static/assets/preview/official').exists() or Path('static/assets/preview/customs').exists():
            path = 'static/assets/preview/' + filename
    with open(path, 'rb') as f:
        data = f.read()

    print("ASSET", filename, len(data), hashlib.md5(data).hexdigest())
    return send_file(path, mimetype='application/octet-stream')

@app.route('/game/rest.php', methods=['POST'])
def game_rest():
    # Inicializando las listas de canciones solo si no tenemos datos
    if not dictCancionesAutorizadas or not dictCancionesCatalogo:
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
    match tipoRequest:
        case 'login':
            tipoContent = {
                'userid': '000001',
                'sessionid': '1',
                'nick': datosRequest['username']
            }

        case 'logout':
            # WORKAROUND: Limpiar las variables de canciones si cerramos el juego.
            #             Esto hace que se re-inicializen si el server está abierto.
            #             (ideal para customs o refrescar nuevas canciones).
            dictCancionesAutorizadas.clear()
            dictCancionesCatalogo.clear()
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
            tipoContent = {
                'songs': dictCancionesCatalogo,
                'table': ""
            }

        case 'getauthorizedsongs':
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
                'table': [
                    {
                      "nick": "JorgePruebas",
                      "score": "1911",
                      "userid": "2",
                      "instrumentid": "GUITAR",
                      "level": "HARD",
                      "gamemode": "cooperative",
                      "songid": "634399367177968750"
                    }
                ],
                'startpos':0
            }

        case 'getads':
            # Flag para activar las falsas publicidades
            mostrarAdsAdicionales=False

            if mostrarAdsAdicionales:
                # Añadiendo variables principales
                pathImagenesServer = os.path.join(get_bundle_dir(), 'static', 'img')
                prefixImagenesAds = "erdtv_ad_"
                listaAdsMainMenu = list(Path(pathImagenesServer).glob(prefixImagenesAds + "mainmenu_*.png"))
                listaAdsMainMenu2 = list(Path(pathImagenesServer).glob(prefixImagenesAds + "mainmenu2_*.png"))
                listaAdsLoading = list(Path(pathImagenesServer).glob(prefixImagenesAds + "loading_*.png"))
                listAdsFinal = []

                # Hagamos que aparezcan random
                magicNumMainMenu = random.randrange(1, 4)
                magicNumMainMenu2 = random.randrange(1, 5)
                magicNumLoading = random.randrange(1, 3)

                if listaAdsMainMenu and magicNumMainMenu == 4:
                    # que ad vamos a elegir?
                    adSeleccionada = listaAdsMainMenu[random.randrange(1, len(listaAdsMainMenu))]
                    # sacar el md5 del ad
                    with open(str(adSeleccionada), 'rb') as f:
                        # Necesario para el hash de la cancion
                        datosAd = f.read()
                    md5AdMainMenu = hashlib.md5(datosAd).hexdigest()
                    # una vez hecho todo, vamos a mandarle la lista
                    nuevaAd = {
                        'hash' : md5AdMainMenu,
                        'server': 'localhost',
                        'path': '/static/img/' + adSeleccionada.stem + '.png',
                        'place': 'mainmenu1'
                    }
                    listAdsFinal.append(nuevaAd)

                if listaAdsMainMenu2:
                    if magicNumMainMenu2 == 3:
                        # que ad vamos a elegir?
                        adSeleccionada = listaAdsMainMenu2[random.randrange(1, len(listaAdsMainMenu2))]
                        # sacar el md5 del ad
                        with open(str(adSeleccionada), 'rb') as f:
                            # Necesario para el hash de la cancion
                            datosAd = f.read()
                        md5AdMainMenu2 = hashlib.md5(datosAd).hexdigest()
                        # una vez hecho todo, vamos a mandarle la lista
                        nuevaAd = {
                            'hash' : md5AdMainMenu2,
                            'server': 'localhost',
                            'path': '/static/img/' + adSeleccionada.stem + '.png',
                            'place': 'mainmenu2'
                        }
                    else:
                        nuevaAd = listaAdsPermanente[0]
                    listAdsFinal.append(nuevaAd)

                if listaAdsLoading:
                    if magicNumLoading == 2:
                        # que ad vamos a elegir?
                        adSeleccionada = listaAdsLoading[random.randrange(1, len(listaAdsLoading))]
                        # sacar el md5 del ad
                        with open(str(adSeleccionada), 'rb') as f:
                            # Necesario para el hash de la cancion
                            datosAd = f.read()
                        md5AdLoading = hashlib.md5(datosAd).hexdigest()
                        # una vez hecho todo, vamos a mandarle la lista
                        nuevaAd = {
                            'hash' : md5AdLoading,
                            'server': 'localhost',
                            'path': '/static/img/' + adSeleccionada.stem + '.png',
                            'place': 'loading'
                        }
                    else:
                        nuevaAd = listaAdsPermanente[1]
                    listAdsFinal.append(nuevaAd)

                # Una vez que ya está todo, enviar la lista definitiva
                tipoContent = {
                    'adverts': listAdsFinal
                }
            else:
                tipoContent = {
                    'adverts': listaAdsPermanente
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
