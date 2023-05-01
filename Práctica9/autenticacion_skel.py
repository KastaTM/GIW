# -*- coding: utf-8 -*-


from flask import Flask, request, session, render_template
from mongoengine import connect, Document, StringField, EmailField, ValidationError

# Resto de importaciones

import bcrypt #Para hashear las contraseñas

import pyotp # Para generar TOTP
import qrcode #Para generar QR en python

import base64 #Para incrustar la imagen en HTML en Base64
from io import BytesIO
from PIL import Image


app = Flask(__name__)
connect('giw_auth')


# Clase para almacenar usuarios usando mongoengine
class User(Document):
	user_id = StringField(primary_key=True)
	full_name = StringField(min_length=2, max_length=50, required=True)
	country = StringField(min_length=2, max_length=50, required=True)
	email = EmailField(required=True)
	passwd = StringField(min_length=4, required=True)
	secret = StringField(required = False)
	def clean(self):
		self.validate(clean=False)
		if(len(self.full_name.split()) != 3): #Debe contener 3 campos, el nombre y 2 apellidos
			raise ValidationError("Nombre completo incorrecto")



##############
# APARTADO 1 #
##############

# 
# Explicación detallada del mecanismo escogido para el almacenamiento de
# contraseñas, explicando razonadamente por qué es seguro
#

"""
El almacenamiento de contraseñas será seguro porque encriptaremos la cadena creando un hash. 
Para una mayor seguridad, utilizaremos una salt aleatoria y el uso de funciones de derivacion, generando el hash 16 veces,
utilizando la librería bcript. Con esto, aumentamos el coste computacional transcurrido, pero mejoramos la seguridad en caso
de que un atacante intente romper el cifrado a fuerza bruta. Bcript utiliza un algoritmo de cifrado Blowfish que aún no se han
encontrado técnicas de criptoanálisis.
Para reforzar aún más la seguridad, podríamos añadir pimienta, inyectando caracteres dentro de la contraseña	.
"""

@app.route('/signup', methods=['POST'])
def signup():
	user_id = request.form["nickname"]
	full_name = request.form["full_name"]
	country = request.form["country"]
	email = request.form["email"]
	passwd = request.form["password"]
	passwd2 = request.form["password2"]
	
	query = User.objects(user_id = user_id)
	if(len(query) == 0): #len sera = 0 si no hay usuario 
		if(passwd == passwd2):
			if(len(passwd) < 4): #Debe contener al menos 4 caracteres
				return "<html><h1> Las contraseñas es demasiado débil </h1></html>"
			modifiedPasswd = passwd.encode() #Es necesario tenerlo como bytes para hacer el hash
			salt = bcrypt.gensalt(rounds=16) #Generamos la salt aleatoria, ejecutada 16 veces para una mayor seguridad
			hashed = bcrypt.hashpw(modifiedPasswd, salt)
			usuario = User(user_id = user_id,full_name = full_name,country = country,email = email, passwd = hashed)
			usuario.save()
			return render_template('welcome.html', name=full_name)
		else:
			return "<html><h1> Las contraseñas no coinciden </h1></html>"
	else:
		return "<html><h1>El usuario ya existe</h1></html>"

	
	


@app.route('/change_password', methods=['POST'])
def change_password():
	user_id = request.form["nickname"]
	old_password = request.form["old_password"].encode()
	new_password = request.form["new_password"].encode()
	query = User.objects(user_id = user_id)	
	if (len(query) == 0 or bcrypt.checkpw(old_password, query[0].passwd.encode()) is False): #Comprueba la contraseña con el hash para comprobar si es realmente esa contraseña
		return "<html><h1>Usuario o contraseña incorrectos </h1></html>"
	else:
		user = User.objects.get(user_id = user_id) #Recogemos el usuario y modificamos la contraseña con un hash nuevo
		salt = bcrypt.gensalt(rounds=16)
		user.passwd = bcrypt.hashpw(new_password, salt).decode()
		user.save()
		return render_template('change_password.html', nickname=user_id)

 
           
@app.route('/login', methods=['POST'])
def login():
	user_id = request.form["nickname"]
	password = request.form["password"].encode()
	query = User.objects(user_id = user_id)	
	if (len(query) == 0 or bcrypt.checkpw(password, query[0].passwd.encode()) is False):
		return "<html><h1>Usuario o contraseña incorrectos </h1></html>"
	else:
		return render_template('welcome.html', name=query[0].full_name)
    

##############
# APARTADO 2 #
##############

# 
# Explicación detallada de cómo se genera la semilla aleatoria, cómo se construye
# la URL de registro en Google Authenticator y cómo se genera el código QR
#
"""
Para la generacion de la clave secreta aleatoria en base32, instalé la libreria pyotp. Dicha clave será almacenada en la BD
junto con la información del Usuario creado: ---> pyotp.random_base32() <---

Una vez generado la clave secreta, se prepara la OTP, generando una URL que se pasará en una imagen QR para la configuracion de Google Aunthenticator.
Para generar la URL, instalamos la librería pyotp y lo configuramos con la clave secreta y una cuenta de email, aunque esto es opcional pero recomendable.
Nosotros elegimos TOTP (basado en tiempo) en vez de HOTP (basado en un contador).
La URL tendrá esta estructura_
otpauth://totp/Secure%20App:alice%40google.com?secret=JBSWY3DPEHPK3PXP

Una vez generado la URL, se genera una QR en base a la URL. Decidimos a generar la QR en python con la librería qrcode para optar a la nota máxima de la práctica.
Con la funcion QRCode() generamos la estructura del QR y lo creamos en forma de PIL IMAGE con make_image()
En vez de generar el fichero y pasarlo de forma estática, incrustamos la imagen en base64 en HTML

Para la parte del login, utilizamos el método verify() de la librería pyotp
"""

@app.route('/signup_totp', methods=['POST'])
def signup_totp():
	user_id = request.form["nickname"]
	full_name = request.form["full_name"]
	country = request.form["country"]
	email = request.form["email"]
	passwd = request.form["password"]
	passwd2 = request.form["password2"]
	
	query = User.objects(user_id = user_id)
	if(len(query) == 0):
		if(passwd == passwd2):
			if(len(passwd) < 4): #Debe contener al menos 4 caracteres
				return "<html><h1> Las contraseñas es demasiado débil </h1></html>"

			secret = pyotp.random_base32()
			modifiedPasswd = passwd.encode() #Es necesario tenerlo como bytes para hacer el hash
			salt = bcrypt.gensalt(rounds=16) #Generamos la salt aleatoria
			hashed = bcrypt.hashpw(modifiedPasswd, salt)
			usuario = User(user_id = user_id,full_name = full_name,country = country,email = email, passwd = hashed, secret = secret)
			usuario.save()

			URL = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name= "grupo02_GIW") #URI para la configuracion Google Authenticator, con el email e issuer_name

			qr = qrcode.QRCode( #Generacion del QR, proporcionando los parametros
    		version=1, #La version 1 indica que la estructura del QR sera una matrix 21x21
    		error_correction=qrcode.constants.ERROR_CORRECT_L, # Controla los tipos de error y los soluciona
   			box_size=10,
   			border=4,)

			qr.add_data(URL) #El contenido del QR sera la URL generada para la configuracion con Google Authenticator
			qr.make(fit=True) # Se genera en blanco y en negro
			img = qr.make_image(fill_color="black", back_color="white")

			im_file = BytesIO() #Transformar Pil Image a base64
			img.save(im_file, format="JPEG")
			im_bytes = im_file.getvalue()  # im_bytes: la imagen en binario
			img64 = base64.b64encode(im_bytes).decode()

			return render_template('QR_TOTP.html', qr= img64, name = full_name, secret = secret)
		else:
			return "<html><h1> Las contraseñas no coinciden </h1></html>"
	else:
		return "<html><h1>El usuario ya existe</h1></html>"

        

@app.route('/login_totp', methods=['POST'])
def login_totp():
	user_id = request.form["nickname"]
	password = request.form["password"].encode()

	qr = request.form["totp"]
	query = User.objects(user_id = user_id)	

	secret = query[0].secret
	totp = pyotp.TOTP(secret) #Generamos de nuevo el TOTP para hacer la comprobación con el código proporcionado por el usuario
	if (len(query) == 0 or bcrypt.checkpw(password, query[0].passwd.encode()) is False or totp.verify(qr) is False):
		return "<html><h1>Usuario o contraseña incorrectos </h1></html>"
	else:
		return render_template('welcome.html', name=query[0].full_name)
  

class FlaskConfig:
    """Configuración de Flask"""
    # Activa depurador y recarga automáticamente
    ENV = 'development'
    DEBUG = True
    TEST = True
    # Imprescindible para usar sesiones
    SECRET_KEY = "giw2020&!_()"
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


if __name__ == '__main__':
    app.config.from_object(FlaskConfig())
    app.run()