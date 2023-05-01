# -*- coding: utf-8 -*-

#
# CABECERA AQUI
#

from flask import Flask, request, session, make_response, render_template
# Resto de importaciones
import hashlib #Para generar el state token
import os #Para generar el state token
import requests #Para realizar peticiones
import json

app = Flask(__name__)


# Credenciales. 
# https://developers.google.com/identity/protocols/oauth2/openid-connect#appsetup
# Copiar los valores adecuados.
CLIENT_ID = #pega aqui tu id de cliente
CLIENT_SECRET = #pega aqui tu secreto de cliente

REDIRECT_URI = 'http://localhost:5000/token'

# Fichero de descubrimiento para obtener el 'authorization endpoint' y el 
# 'token endpoint'
# https://developers.google.com/identity/protocols/oauth2/openid-connect#authenticatingtheuser
DISCOVERY_DOC = 'https://accounts.google.com/.well-known/openid-configuration'

# token_info endpoint para extraer información de los tokens en depuracion, sin
# descifrar en local
# https://developers.google.com/identity/protocols/OpenIDConnect#validatinganidtoken
TOKENINFO_ENDPOINT = 'https://oauth2.googleapis.com/tokeninfo'

#Genera una pagina html con un enlace o un boton que redirige al usuario
#a la pagina de autenticacion delegada de google. Esta peticion debe
#contener las credenciales necesarias de nuestra aplicacion web
@app.route('/login_google', methods=['GET'])
def login_google():

    #Creamos el state token y lo almacenamos en session para
    #validarlo más tarde
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    session['state'] = state
    
    #Obtenemos la ruta de autorizacion mediante el documento de descubrimiento de Google
    var = requests.get(url=DISCOVERY_DOC).json()
    aEndpoint = var['authorization_endpoint']
    #Construimos la url con los parámetros adecuados
    auth_url = aEndpoint + "?client_id=" + CLIENT_ID + "&response_type=code&scope=openid%20email&redirect_uri=" + REDIRECT_URI + "&state=" + state
    
    #Mostramos la pagina HTML con el botón que redirigirá a la autenticación delegada
    #¡IMPORTANTE! el archivo 'index.html' debe estar en la carpeta templates
    response = make_response(
        render_template('index.html',
                        CLIENT_ID=CLIENT_ID,
                        STATE=state,
                        auth_url=auth_url))
    return response

    #También se puede devolver directamente render_template, como mostramos a continuación y como realizabamos
    #en la práctica anterior, pero hemos seguido las pautas que aparecen en https://developers.google.com/identity/protocols/oauth2/openid-connect#python

    #return render_template('index.html', auth_url=auth_url)



#Recibe la peticion del usuario redirigida desde Google con el codigo
#temporal que deberemos canjear por un id_token. Por tanto, en las 
#credenciales de nuestra aplicación deberemos configurar el redirect_uri
#a http://localhost:5000/token tal y como aparece en el esqueleto. El
#id_token que obtendremos será un JWT con la información del usuario, del
#que extraeremos la dirección de e-mail (consultar las referencias). Finalmente
#se generará una página HTML de bienvenida con el mensaje Bienvenido <e-mail>
@app.route('/token', methods=['GET'])
def token():
    # Nos aseguramos de que la peticion no es una falsificacion (forgery)
    # y de que el usuario que envia la petición es quien dice ser
    # comprobando que el state token generado anteriormente coincide con el recibido
    aux = request.args.get('state') #state token recibido
    aux2 = session['state'] #state token generado previamente
    if aux != aux2:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtenemos el código que utilizaremos para obtener el ID token
    codigo = request.args.get('code')

    #Obtenemos la ruta de token mediante el documento de descubrimiento de Google
    var = requests.get(url=DISCOVERY_DOC).json()
    tEndpoint = var['token_endpoint']
    #Construimos la url con los parámetros adecuados
    token_url = tEndpoint + "?code=" + codigo + "&client_id="+CLIENT_ID+"&client_secret="+CLIENT_SECRET+"&redirect_uri="+REDIRECT_URI+"&grant_type=authorization_code"
    #Enviamos la peticion POST para recibir  el ID_token
    respuesta = requests.post(url=token_url)

    #Si se produce algun error, mostramos una página html que nos avisa
    if not respuesta.ok:
        return make_response(
            render_template('error.html'))

    # Extraemos el ID token
    idToken = respuesta.json()['id_token']
    # Obtenemos la información que contiene el ID token en formato JWT (JSON Web Token)
    respuesta2 = requests.get(url=TOKENINFO_ENDPOINT, params={"id_token": idToken})

    #Si se produce algun error, mostramos una pagina html que nos avisa
    if not respuesta2.ok:
        return make_response(
            render_template('error.html'))

    #Convertimos la información
    datos = respuesta2.json()

    #Mostramos la página de bienvenida con la dirección de email
    return make_response(
        render_template('bienvenida.html',
                        email=datos['email']))


        
class FlaskConfig:
    '''Configuración de Flask'''
    # Activa depurador y recarga automáticamente
    ENV = 'development'
    DEBUG = True
    TEST = True
    # Imprescindible para usar sesiones
    SECRET_KEY = 'giw2020&!_()'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


if __name__ == '__main__':
    app.config.from_object(FlaskConfig())
    app.run()