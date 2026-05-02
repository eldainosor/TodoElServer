# Todo el server
Simulador de servidor para el juego El Rock de Tu Vida

## Contexto
El Rock de tu vida es un juego hecho por Next Level Games y publicado por Loaded.vg en 2011. Su objetivo era permitir al público argentino disfrutar de la experiencia de juegos como Guitar Hero o Rock Band con música de Rock de Argentina y Uruguay permitiendo el uso de 4 instrumentos y ofreciendo un servicio de canciones adquiribles usando SMS.
Este juego dejó de funcionar en 2014 y al apagarse los servidores, el juego no puede pasar del inicio de sesión, ya que llama a www.elrockdetuvida.com y no responde.

## Sobre el servidor

Revisando el ejecutable del juego, encontramos que siempre llama a /game/rest.php con unos valores y un tipo de request. Las requests pueden ser:
- `login` (inicio de sesión)
- `logout` (cerrar sesión cuando cierra el juego)
- `getads` (anuncios en la pantalla de carga de canciones)
- `getticker` (texto para mostrar en el área superior del juego)
- `getauthorizedsongs` (ids y hashes que dejan que el usuario pueda jugar)
- `getallsongs` (lista de canciones disponibles en el catálogo de canciones)
- `gethighscore` (obtener el puntaje alto del usuario?)
- `gethighscorepos` (obtiene en que posición de puntajes altos está el usuario?)
- `submithighscore` (guarda el puntaje del usuario en el server)

Este servidor provee respuestas a estos requests para permitir el funcionamiento del juego, pero queda pendiente:
- Guardar los puntajes del usuario y verificar posibles puntajes
- Generar archivos válidos para getads (solo por motivos de documentación)
- Ver la implementación del multijugador?

Para la generación de `getallsongs` y `getauthorizedsongs` se requiere tener los archivos dentro del directorio donde está el servidor. Para cambiar esto o preparar el ejecutable para su instalación, vaya a **Instrucciones de instalación y uso**.


## Instrucciones de instalación y uso
Para poder usar este servidor, se recomienda usar Python 3.4 en adelante.
### Para ejecutar el script normalmente:
1. Generar un entorno virtual de python
    ```
    python -m venv .venv
    ```

2. Instalar las siguientes dependencias:
	```
	pip install -r requirements.txt
	```

3. Una vez instalado, exportar el directorio en donde se está ejecutando:

	En Windows:
	```
	set "TES_DIR_JUEGO=[DIRECTORIO_DEL_JUEGO_INSTALADO]"
	```
	En Linux (no está verificado):
	```
	export TES_DIR_JUEGO="[DIRECTORIO_DEL_JUEGO_INSTALADO]"
	```

	*Nota: Este paso es solo si querés modificar el código del ejecutable y hacer pruebas. Para su uso permanente, es recomendado generar el standalone y seguir los pasos de abajo.*

4. Ejecutar el script usando
	```
	flask run
	```

### Para generar el servidor standalone:
1. Ejecutar los pasos 1 y 2 de "Para ejecutar el script normalmente".

2. Instalar PyInstaller en nuestro entorno virtual:
	```
	pip install -r requirements_build.txt
	```

3. Una vez instalado, empaquetar el script
	```
	pyinstaller --onefile --name TodoElServer --icon=todoelrock.ico erdtvserver.py 
	```

4. Mover el binario que se encuentra en dist a la carpeta de instalación del juego.

## Observación sobre el ejecutable del juego (erdtv.exe)
Es obligatorio que el juego use un ejecutable modificado para redirigir las llamadas al servidor a nuestro servidor local. Podés descargar [nuestro ejecutable modificado acá](https://drive.google.com/file/d/1vbQYR7SwGN60o17wsSNFs9OEidAZ-ybt/view?usp=sharing) ([resultados de virustotal](https://www.virustotal.com/gui/file-analysis/ZGY2OTFjM2M1OWZiMzg2YTFiZTc3MWI3YWUyNWRkNGI6MTc3NTE3Nzg2OA==)).
En caso de que no confíes en nuestro ejecutable y sabés usar herramientas para modificar EXEs (como Ghidra), podés seguir los pasos de abajo.

###  Modificando el ejecutable manualmente
El juego, en la dirección `004151b0` realiza la comunicación con el servidor. En la dirección `0047d6c4` el juego especifica el puerto en el que se comunica (puerto 80) y en la dirección `004151fb` especifica la URL que va a usar para este llamado (`u"www.elrockdetuvida.com"`).  
Para garantizar la compatibilidad con nuestro servidor, se recomienda cambiar los siguientes valores que están en estas direcciones:
- `0046b9de`: `u"Awww.elrockdetuvida.com"` -> `u"Alocalhost"`
- `0047d6c4`: `50 00` -> `1D 12`

Esto hace que, en vez de llamar a www.elrockdetuvida.com en el puerto 80, llame al localhost en el puerto 4637.