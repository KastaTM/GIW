"""
GIW 2022-23
Práctica 07
Grupo 09
Autores: Rodrigo Castañón Martínez, David Lago Hernández, Daniel Muñoz García, Ignacio Urretavizcaya Tato


Rodrigo Castañón Martínez, David Lago Hernández, Daniel Muñoz García, Ignacio Urretavizcaya Tato 
declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos sido
ayudados por ninguna otra persona ni hemos obtenido la solución de fuentes externas, y tampoco 
hemos compartido nuestra solución con nadie. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los resultados
de los demás.
"""
from flask import Flask, request, session, render_template
app = Flask(__name__)

idAsignatura = 0
asignaturas = []

###
### <DEFINIR AQUI EL SERVICIO REST>
###

def asignaturaValida(asignatura):
    valida = False
    if "nombre" in asignatura and "numero_alumnos" in asignatura and "horario" in asignatura and len(asignatura.keys()) == 3 and type(asignatura["nombre"]) is str and type(asignatura["numero_alumnos"]) is int and type(asignatura["horario"]) is list:
            valida = True
            for horario in asignatura["horario"]:
                if(type(horario) is dict and "dia" in horario and "hora_inicio" in horario and "hora_final" in horario and len(horario.keys()) == 3 and type(horario["dia"]) is str and type(horario["hora_inicio"]) is int and type(horario["hora_final"]) is int):
                    valida = True
                else:
                    valida = False
                    break
    return valida

def campo_valido(campo):
    if "nombre" in campo and isinstance(campo.get("nombre"), str) and len(campo) == 1:
        return "nombre"
    elif "numero_alumnos" in campo and isinstance(campo.get("numero_alumnos"), int) and len(campo) ==1:
        return "numero_alumnos"
    elif "horario" in campo and isinstance(campo.get("horario"), list) and len(campo) == 1:
        return "horario"
    else:
        return None


@app.route('/asignaturas', methods=['DELETE'])
def eliminarAsignaturas():
    global idAsignatura 
    idAsignatura = 0
    asignaturas.clear()
    return "No Content", 204

@app.route('/asignaturas', methods=['POST'])
def anadirAsignatura():
    estadoHTTP = 400 
    asignatura = request.get_json()
    ret = ""
    if(asignaturaValida(asignatura)):
        estadoHTTP = 201
        global idAsignatura 
        idAsignatura += 1
        asignatura['id'] = idAsignatura
        asignaturas.append(asignatura)
        ret = {'id' : idAsignatura}

    return ret, estadoHTTP


@app.route('/asignaturas', methods=['GET'])
def listarAsignaturas():
    numPagina = request.args.get("page", None)
    asignaturasPorPagina = request.args.get("per_page", None)  
    cuantosAlumnos = request.args.get("alumnos_gte", 0)
    listaFiltrada = []
    estadoHTTP = 200
    if numPagina is None and asignaturasPorPagina is not None or numPagina is not None and asignaturasPorPagina is None:
        estadoHTTP = 400
    else:
        if len(asignaturas) > 0:
            for asignatura in asignaturas:
                if asignatura["numero_alumnos"] >= int(cuantosAlumnos):
                    url = "/asignaturas/" + str(asignatura["id"])
                    listaFiltrada.append(url)
                else:
                    estadoHTTP = 206
            if numPagina is not None and asignaturasPorPagina is not None:  
                cont = 0
                listaPaginada = []
                for i in range(int(numPagina)):
                    for j in range(int(asignaturasPorPagina)):
                        if cont == len(listaFiltrada) :
                            break   
                        if i + 1 == int(numPagina):
                            listaPaginada.append(listaFiltrada[cont])
                        cont += 1
                if len(listaPaginada) < len(listaFiltrada):
                    estadoHTTP = 206
                listaFiltrada = listaPaginada

    return {"asignaturas" : listaFiltrada}, estadoHTTP

@app.route('/asignaturas/<int:id>', methods=['DELETE'])
def borrar_asignatura(id):
    global asignaturas
    for i in asignaturas:
        if i.get("id") == id:
            asignaturas.remove(i)
            return "No Content", 204
    return "Not Found", 404

@app.route('/asignaturas/<int:id>', methods=['GET'])
def mostrar_asignatura(id):
    global asignaturas
    for i in asignaturas:
        if i.get("id") == id:
            return i
    return "Not Found", 404  

@app.route('/asignaturas/<int:id>', methods=['PUT'])
def actualizar_asignatura(id):
    global asignaturas
    asignatura = request.get_json()
   
    for i in range(len(asignaturas)):
        if asignaturas[i].get("id") == id:
            if(asignaturaValida(asignatura)):
                aux = {}
                aux["id"] = id
                aux.update(asignatura)
                asignaturas[i] = aux
                return "OK", 200 
            else:
                return "Bad Request", 400
    return "Not Found", 404
        
    
@app.route('/asignaturas/<int:id>', methods=['PATCH'])
def actualizar_campo(id):
    global asignaturas
    campo = request.get_json()
    key = campo_valido(campo)
    for i in range(len(asignaturas)):
        if asignaturas[i].get("id") == id:
            if key != None:
                asignaturas[i][key] = campo[key]
                return "OK", 200
            else:
                return "Bad Request", 400
    return "Not Found", 404
        
@app.route('/asignaturas/<int:id>/horario', methods=['GET'])
def mostrar_horario(id):
    global asignaturas
    for i in asignaturas:
        if i.get("id") == id:
            ret = {}
            ret["horario"] = i.get("horario")
            return ret
    return "Not Found", 404  

class FlaskConfig:
    """Configuración de Flask"""
    # Activa depurador y recarga automáticamente
    ENV = 'development'
    DEBUG = True
    TEST = True
    # Imprescindible para usar sesiones
    SECRET_KEY = "giw_clave_secreta"
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


if __name__ == '__main__':
    app.config.from_object(FlaskConfig())
    app.run()