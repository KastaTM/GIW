"""
Práctica 8
Grupo 9
David Lago Hernández
Ignacio Urretavizcaya Tato
Rodrigo Castañón Martínez
Daniel Muñoz García


David Lago Hernández, Ignacio Urretavizcaya Tato, Rodrigo Castañón Martínez y Daniel Muñoz García
declaramos que esta solución es fruto exclusivamente
de nuestro trabajo personal. No hemos sido ayudados por ninguna otra persona ni hemos
obtenido la solución de fuentes externas, y tampoco hemos compartido nuestra solución
con nadie. Declaramos además que no hemos realizado de manera deshonesta ninguna otra
actividad que pueda mejorar nuestros resultados ni perjudicar los resultados de los demás.
"""


from mongoengine import *
import math
con = connect(db='giw_mongoengine', uuidRepresentation='standard')


class Tarjeta(EmbeddedDocument):
 nombre = StringField(required=True,min_length = 2)
 numero = StringField(required=True, max_length = 16, regex = "[0-9]{16}")
 mes = StringField(required=True, max_length = 2, regex = "[0-9]{2}")
 año = StringField(required=True, max_length = 2, regex = "[0-9]{2}")
 ccv = StringField(required=True, max_length = 3, regex = "[0-9]{3}")

class Producto(Document):
 codigo_barras = StringField(required=True,unique=True, max_length = 13,regex = "^[0-9]{13}$")
 nombre = StringField(required=True,min_length = 2,regex = "([a-zA-Z][^\S])*")
 categoria_principal = IntField(required=True, min_value = 0)
 categorias_secundarias = ListField(IntField(min_value = 0))
 def clean(self):
  self.validate(clean=False)
  if len(self.categorias_secundarias) != 0:
    if self.categoria_principal != self.categorias_secundarias[0]:
     raise ValidationError("La categoría principal del producto no aparece en el primer lugar de la lista de las categorias secundarias")
  
  arr_codigo_barras = list(self.codigo_barras)
  cont = 0
  sum_par = 0
  sum_impar = 0
  control = arr_codigo_barras.pop()

  for x in arr_codigo_barras:
    if cont % 2:
     sum_impar += int(x)
    else:
     sum_par += int(x)
    cont+=1
  sum_total = sum_par + sum_impar*3
  redondeado = math.ceil(sum_total/10)*10
  control_bueno = redondeado-sum_total
  if int(control) != int(control_bueno):
    raise ValidationError("El codigo de control es erroneo")



class Linea(EmbeddedDocument):
 num_items = DecimalField(required=True, min_value = 1)
 precio_item = DecimalField(required=True, min_value = 0.01)
 nombre_item = StringField(required=True,min_length = 2,regex = "([a-zA-Z][^\S])*")
 total = DecimalField(required=True)
 ref = ReferenceField(Producto, required=True)

 def clean(self):
  self.validate(clean=False)
  total_real = self.num_items * self.precio_item
  if total_real != self.total:
     raise ValidationError("El total no es el que corresponde")
  if self.nombre_item != self.ref.nombre:
     raise ValidationError("Los nombres no coinciden")
   

class Pedido(Document):
 total = DecimalField(required=True, min_value = 0.01)
 fecha = ComplexDateTimeField(required=True)
 lineas = ListField(EmbeddedDocumentField(Linea))

 def clean(self):
    self.validate(clean = False)
    total_lineas = 0
    nombre_lineas = []
    for x in self.lineas:
     total_lineas += x.total
     if(x.nombre_item not in nombre_lineas):
      nombre_lineas.append(x.nombre_item)
     else:
      raise ValidationError("Dos lineas con mismo nombre")
    if total_lineas != self.total:
     raise ValidationError("No coinciden los totales")
    


class Usuario(Document):
 dni = StringField(required=True, unique=True,regex = "[0-9]{8}[A-Z]{1}")
 nombre = StringField(required=True,min_length = 2)
 apellido1 = StringField(required=True,min_length = 2)
 apellido2 = StringField(required=False,min_length = 2)
 f_nac = StringField(required=True, min_length = 10,max_length = 10,regex = "[0-9]{4}[-]{1}[0-9]{2}[-]{1}[0-9]{2}")
 tarjetas = ListField(EmbeddedDocumentField(Tarjeta))
 pedidos = ListField(ReferenceField(Pedido, reverse_delete_rule=PULL))
 
 def clean(self):
    self.validate(clean = False)
    dni_array = ["T","R","W","A","G","M","Y","F","P","D","X","B","N","J","Z","S","Q","V","H","L","C","K","E"]
    dni_sin_letra = self.dni[:-1]
    dni_letra = self.dni[-1]
    resto = int(dni_sin_letra)%23
    if dni_array[resto] != dni_letra:
     raise ValidationError("DNI mal escrito")

