# Todo el server
Simulador de servidor para el juego El Rock de Tu Vida

## Contexto
El Rock de tu vida es un juego hecho por Next Level Games y publicado por Loaded.vg en 2011. Su objetivo era permitir al público argentino disfrutar de la experiencia de juegos como Guitar Hero o Rock Band con música de Rock de Argentina y Uruguay permitiendo el uso de 4 instrumentos y ofreciendo un servicio de canciones adquiribles usando SMS.
Este juego dejó de funcionar en 2014 y al apagarse los servidores, el juego no puede pasar del inicio de sesión, ya que llama a www.elrockdetuvida.com y no responde.
Este proyecto busca restaurar alguna de las funcionalidades del juego al generar un servidor que genere respuestas que el juego necesite para hacerlo funcional.

## Sobre el servidor

Revisando el ejecutable del juego, encontramos que siempre llama a /game/rest.php con unos valores y un tipo de request. Las requests pueden ser:
- `login` (inicio de sesión e ID de sesión del usuario)
- `logout` (cerrar sesión cuando cierra el juego)
- `getads` (anuncios en la pantalla de inicio y carga de canción)
- `getticker` (texto para mostrar en el área superior del juego)
- `getauthorizedsongs` (ids y hashes que permiten al usuario jugar las canciones que tiene instaladas)
- `getallsongs` (lista de canciones disponibles en el catálogo de canciones, el juego solo muestra las que el usuario no tiene)
- `gethighscore` (obtener el puntaje alto del usuario?)
- `gethighscorepos` (obtiene en que posición de puntajes altos está el usuario?)
- `submithighscore` (guarda el puntaje del usuario en el server)

Este servidor actualmente puede realizar lo siguiente:
- Verificación basica del usuario para iniciar sesión (deja entrar al juego con cualquier usuario y contraseña)
- Proveedor de canciones disponibles en el catálogo
- Verificación de canciones autorizadas
- Proveedor de archivos externos para el catálogo (carátulas y vista previa de las canciones)
- Proveedor de publicidades (solo publicidades esenciales activadas por defecto)

Todavía queda pendiente trabajar en los siguientes elementos:
- Guardar los puntajes del usuario y verificar posibles puntajes
- Ver la implementación del multijugador?
- Optimización y arreglos en partes del código como la petición de archivos del catálogo
- Implementar el catálogo online extraído de un archivo JSON remoto, con posibilidad de acceder a una copia offline incluída en el binario hecho con PyInstaller.

Para la generación de `getallsongs` y `getauthorizedsongs` se requiere tener los archivos dentro del directorio donde está el servidor. Para cambiar esto o preparar el ejecutable para su instalación, vaya a **Instrucciones de instalación y uso**.


## Instrucciones de instalación y uso
Para poder usar este servidor, se recomienda usar Python 3.10 en adelante.

### Para ejecutar el script normalmente:
1. Generar un entorno virtual de python
    ```
    python -m venv .venv
    ```

2. Instalar las siguientes dependencias:
	```
	pip install flask python-dotenv
	```

3. Una vez instalado, exportar el directorio en el que se encuentra tu instalación de El Rock de Tu Vida:

	En Windows (batch):
	```
	set "TES_DIR_JUEGO=[DIRECTORIO_DEL_JUEGO_INSTALADO]"
	```

	o su equivalente en PowerShell:
	```
	$env:TES_DIR_JUEGO = "[DIRECTORIO_DEL_JUEGO_INSTALADO]"
	```

	En Linux (no está verificado):
	```
	export TES_DIR_JUEGO="[DIRECTORIO_DEL_JUEGO_INSTALADO]"
	```

	*Nota: Se recomienda hacer esta declaración para que el script sepa en donde están los archivos para el catálogo y autorización. Este paso es solo si querés modificar el código del server y hacer pruebas. Para su uso permanente, es recomendado generar el standalone y seguir los pasos de abajo.*

4. Ejecutar el script usando
	```
	flask run
	```

### Para generar el servidor standalone:
1. Ejecutar los pasos 1 y 2 de "Para ejecutar el script normalmente".

2. Instalar PyInstaller en nuestro entorno virtual:
	```
	pip install pyinstaller
	```

3. Una vez instalado, empaquetar el script
	```
	pyinstaller --onefile --name TodoElServer --icon=todoelrock.ico  --add-data "static;static" erdtvserver.py 
	```

4. Mover el binario ejecutable que se encuentra en la carpeta `dist` a la carpeta de instalación del juego (debe estar en la misma carpeta en donde se encuentra `erdtv.exe`).

## Funcionamiento con el ejecutable (erdtv.exe)
Este servidor Flask funciona por defecto en el puerto `4637`. Flask requiere permisos de administrador para poder usar el puerto HTTP (80) por defecto. Esto lleva a que se deba modificar el ejecutable del juego para poder integrar nuestro servidor... o usarlo sin enpaquetarlo con PyInstaller.

###  Método 1: Modificando el ejecutable y usando el servidor compilado con PyInstaller
El juego realiza comunicaciones al servidor para la comunicación con su API (`game/rest.php`) y los datos a descargar del catálogo. En la dirección `[puerto_del_server]` el juego especifica el puerto en el que se comunica (puerto `80`) y en la dirección `[url_del_server]` especifica la URL que va a usar para este llamado (`u"www.elrockdetuvida.com"`). Adicionalmente, en el apartado de `[puerto_request_descargas]` se va a encontrar una instrucción que busca unir la URL del server con el puerto 80 para descargar vistas previas y carátulas para mostrar en el catálogo.

Según investigaciones, el juego tiene 3 versiones: La versión 1.0.0.0 (lanzamiento oficial, comprada en Musimundo/Garbarino), La versión 1.0.0.6 (disco que venía de regalo con computadoras Lenovo) y la versión 1.0.0.14 (disco azul, lanzado en 2012). Según la versión que tengas, vas a tener que buscar la siguiente dirección en el ejecutable:
| Nombre del valor | Versión 1.0.0.0 | Versión 1.0.0.6 | Versión 1.0.0.14 |
|--------|-----|-----------|-----------|
| `url_del_server` | `0046b8fe`  | `0046b9de`  | `0046c9f2`  |
| `puerto_del_server` | `0047d6c4`  | `0047d6c4` | `0047e6c4` |
| `puerto_request_descargas` | `00414460`  | `00414470` | `00414520` |

Para garantizar que el juego se comunique con nuestro servidor, se recomienda usar **Ghidra** o **x86dbg** para cambiar los siguientes valores que están en las direcciones correspondientes al ejecutable que tengas:
- `url_del_server`: `u"Awww.elrockdetuvida.com"` -> `u"Alocalhost"`
- `puerto_del_server`: `50 00` -> `1D 12`
- `puerto_request_descargas`: `[ESI + 0x40c],0x50` -> `[ESI + 0x40c],0x121D`

Esto hace que, en vez de llamar a www.elrockdetuvida.com en el puerto 80, llame al localhost en el puerto 4637.

###  Método 2: Ejecutando el server en tiempo real sin modificar el ejecutable
Esto evita el modificar el ejecutable, pero hace que siempre que se quiera usar el servidor con el juego, se deba abrir una ventana con Python para ejecutarlo. Es tedioso comparado a modificar el ejecutable pero es un camino alternativo.

Primero, debemos modificar nuestro fichero hosts (en Windows, se encuentra en `C:\Windows\System32\drivers\etc\hosts`) y añadir la siguiente entrada:
```
	127.0.0.1 www.elrockdetuvida.com
```

Una vez hecho esto, debemos abrir una instancia de cmd o powershell como **administrador**. Vamos a seguir los pasos de [Para ejecutar el script normalmente](#para-ejecutar-el-script-normalmente) (omitiendo los pasos 1 y 2 en caso de que ya estén hechos). 
En el paso 4, ejecutamos `flask run --port 80`. 

El servidor debería funcionar para recibir requests del juego sin problemas.
