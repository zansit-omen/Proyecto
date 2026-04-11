import sqlite3
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import os
from pymongo import MongoClient
# Se importan los chats del archivo que hizo la conexion a mongoDB para mantener el codigo de la API más simple
from mongo_chat import chats
from mongo_chat import obtener_chats_usuario
from mongo_chat import ver_chat
from mongo_chat import enviar_mensaje
from mongo_chat import crear_chat
from datetime import datetime

app = Flask(__name__)
CORS(app)
#database es la base de datos relacional SQL
database = "ProLink.db"

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- LOGIN --------------------
@app.route("/login", methods=["POST"])
def login():
    # Detect if request contains JSON or form data
    if request.is_json:
        data = request.get_json()
        correo = data.get("correo")
        password = data.get("password")
    else:
        correo = request.form.get("correo")
        password = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    usuario = cursor.execute(
        "SELECT * FROM usuario WHERE correo = ?", (correo,)
    ).fetchone()
    conn.close()

    if usuario is None:
        return jsonify({"error": "Correo no encontrado"}), 404
    if usuario["password"] != password:
        return jsonify({"error": "Contraseña incorrecta"}), 401

    # If request came from a web form, redirect to the appropriate dashboard
    if not request.is_json:
        tipoU = usuario["tipoUsuario"]
        idU = usuario["Id"]
        if tipoU == "delegado":
            return redirect(f"/delegado/{idU}")
        elif tipoU == "candidato":
            return redirect(f"/candidato/{idU}")
        else:
            return jsonify({"error": "Tipo de usuario desconocido"}), 400

    # JSON response for API clients
    return jsonify({
        "message": "Login exitoso",
        "id": usuario["Id"],
        "tipoUsuario": usuario["tipoUsuario"]
    })

# -------------------- OFERTAS (Ofertas laborales) --------------------
@app.route("/delegado/<int:idU>/oferta", methods=["GET"])
def obtener_ofertas(idU):
    conn = get_db_connection()
    cursor = conn.cursor()
    ofertas = cursor.execute("SELECT * FROM oferta").fetchall()
    conn.close()
    if not ofertas:
        return jsonify({"error": "No hay ofertas"}), 404
    return jsonify([dict(row) for row in ofertas])

@app.route("/delegado/<int:idU>/oferta/<int:idOferta>", methods=["GET"])
def buscar_oferta(idU, idOferta):
    conn = get_db_connection()
    cursor = conn.cursor()
    oferta = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (idOferta,)
    ).fetchone()
    conn.close()
    if not oferta:
        return jsonify({"error": "No existe la oferta"}), 404
    oferta = dict(oferta)
    return jsonify({
        "titulo": oferta["titulo"],
        "descripcion": oferta["descripcionOferta"],
        "profesion": oferta["profesionBuscar"],
        "estado": "Abierta" if oferta["estadoOferta"] == 1 else "Cerrada"
    })

@app.route("/delegado/<int:idU>/oferta/crear", methods=["POST"])
def crear_oferta(idU):
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json()
        titulo = data.get("titulo")
        descripcion = data.get("descripcionOferta")
        profesion = data.get("profesionBuscar")
    else:
        titulo = request.form.get("titulo")
        descripcion = request.form.get("descripcionOferta")
        profesion = request.form.get("profesionBuscar")

    if not titulo or not descripcion or not profesion:
        return jsonify({"error": "Datos no válidos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT empresaId FROM delegado WHERE Id = ?", (idU,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute("""
        INSERT INTO oferta (titulo, empresaId, descripcionOferta, profesionBuscar)
        VALUES (?, ?, ?, ?)
    """, (titulo, row["empresaId"], descripcion, profesion))
    oferta_id = cursor.lastrowid
    conn.commit()

    # Fetch the created offer
    new_oferta = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (oferta_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(new_oferta))

@app.route("/delegado/<int:idU>/oferta/<int:ofertaId>", methods=["DELETE"])
def eliminar_oferta(idU, ofertaId):
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (ofertaId,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Oferta no encontrada"}), 404
    oferta = dict(row)
    cursor.execute("DELETE FROM oferta WHERE ofertaId = ?", (ofertaId,))
    conn.commit()
    conn.close()
    return jsonify(oferta)

@app.route("/delegado/<int:idU>/oferta/eliminar", methods=["POST"])
def eliminar_oferta_form(idU):
    conn = get_db_connection()
    cursor = conn.cursor()
    oferta_id = request.form.get("ofertaId")
    if not oferta_id:
        conn.close()
        return jsonify({"error": "ID de oferta requerido"}), 400
    row = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (oferta_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Oferta no encontrada"}), 404
    oferta = dict(row)
    cursor.execute("DELETE FROM oferta WHERE ofertaId = ?", (oferta_id,))
    conn.commit()
    conn.close()
    return jsonify(oferta)

@app.route("/delegado/<int:idU>/oferta/<int:oferta_id>", methods=["PUT"])
def actualizar_oferta(idU, oferta_id):
    data = request.get_json()
    titulo = data.get("titulo")
    descripcion = data.get("descripcionOferta")
    profesion = data.get("profesionBuscar")
    estado = data.get("estadoOferta")

    if not titulo or not descripcion or not profesion:
        return jsonify({"error": "Datos no válidos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    oferta = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (oferta_id,)
    ).fetchone()
    if not oferta:
        conn.close()
        return jsonify({"error": "Oferta no encontrada"}), 404

    cursor.execute("""
        UPDATE oferta
        SET titulo = ?, descripcionOferta = ?, profesionBuscar = ?, estadoOferta = ?
        WHERE ofertaId = ?
    """, (
        titulo,
        descripcion,
        profesion,
        estado if estado is not None else oferta["estadoOferta"],
        oferta_id
    ))
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (oferta_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(updated))

# -------------------- POSTULACIONES --------------------
@app.route("/delegado/<int:idU>/oferta/<int:idOferta>/postulacion", methods=["GET"])
def ver_postulaciones(idU, idOferta):
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM postulacion WHERE ofertaId = ?", (idOferta,)
    ).fetchall()
    conn.close()
    if not rows:
        return jsonify({"error": "No hay postulaciones"}), 404
    return jsonify([dict(r) for r in rows])

@app.route("/delegado/<int:idU>/oferta/<int:idOferta>/postulacion/<int:idPostulacion>/aceptar", methods=["PUT"])
def aceptar_postulacion(idU, idOferta, idPostulacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE postulacion SET estadoPostulacion = 1 WHERE postulacionId = ?",
        (idPostulacion,)
    )
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (idPostulacion,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Postulación no encontrada"}), 404
    return jsonify(dict(updated))

@app.route("/delegado/<int:idU>/oferta/<int:idOferta>/postulacion/<int:idPostulacion>/rechazar", methods=["PUT"])
def rechazar_postulacion(idU, idOferta, idPostulacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE postulacion SET estadoPostulacion = 0 WHERE postulacionId = ?",
        (idPostulacion,)
    )
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (idPostulacion,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Postulación no encontrada"}), 404
    return jsonify(dict(updated))

@app.route("/delegado/<int:idU>/oferta/postulacion/<int:idPostulacion>/aceptar", methods=["POST"])
def aceptar_candidato(idU, idPostulacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE postulacion SET estadoPostulacion = 1 WHERE postulacionId = ?",
        (idPostulacion,)
    )
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (idPostulacion,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Postulación no encontrada"}), 404
    return jsonify(dict(updated))

@app.route("/delegado/<int:idU>/oferta/postulacion/<int:idPostulacion>/rechazar", methods=["POST"])
def rechazar_candidato(idU, idPostulacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE postulacion SET estadoPostulacion = 0 WHERE postulacionId = ?",
        (idPostulacion,)
    )
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (idPostulacion,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Postulación no encontrada"}), 404
    return jsonify(dict(updated))

# -------------------- EMPRESAS --------------------
@app.route("/delegado/<int:idU>/empresa", methods=["POST"])
def crear_empresa(idU):
    data = request.get_json()
    razonSocial = data.get("razonSocial")
    correo_contacto = data.get("correoContacto")
    direccion = data.get("direccion")
    if not razonSocial or not correo_contacto or not direccion:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO empresa (razonSocial, correoContacto, direccion) VALUES (?, ?, ?)",
        (razonSocial, correo_contacto, direccion)
    )
    empresa_id = cursor.lastrowid
    conn.commit()
    new_empresa = cursor.execute(
        "SELECT * FROM empresa WHERE empresaid = ?", (empresa_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(new_empresa))

@app.route("/delegado/<int:idU>/empresa/<int:empresaid>", methods=["GET"])
def mostrar_empresa(idU, empresaid):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = cursor.execute(
        "SELECT * FROM empresa WHERE empresaid = ?", (empresaid,)
    ).fetchone()
    conn.close()
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(dict(empresa))

@app.route("/delegado/<int:idU>/empresa/<int:empresaid>", methods=["PUT"])
def actualizar_empresa(idU, empresaid):
    data = request.get_json()
    razonSocial = data.get("razonSocial")
    correo_contacto = data.get("correoContacto")
    direccion = data.get("direccion")
    if not razonSocial or not correo_contacto or not direccion:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE empresa SET razonSocial = ?, correoContacto = ?, direccion = ? WHERE empresaid = ?",
        (razonSocial, correo_contacto, direccion, empresaid)
    )
    conn.commit()
    updated = cursor.execute(
        "SELECT * FROM empresa WHERE empresaid = ?", (empresaid,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(dict(updated))

@app.route("/delegado/<int:idU>/empresa/<int:empresaid>", methods=["DELETE"])
def eliminar_empresa(idU, empresaid):
    conn = get_db_connection()
    cursor = conn.cursor()
    empresa = cursor.execute(
        "SELECT * FROM empresa WHERE empresaid = ?", (empresaid,)
    ).fetchone()
    if not empresa:
        conn.close()
        return jsonify({"error": "Empresa no encontrada"}), 404
    empresa_dict = dict(empresa)
    cursor.execute("DELETE FROM empresa WHERE empresaid = ?", (empresaid,))
    conn.commit()
    conn.close()
    return jsonify(empresa_dict)

# -------------------- DELEGADOS --------------------
@app.route("/crear-delegado", methods=["POST"])
def crear_delegado():
    data = request.get_json()
    usuario_id = data.get("usuarioId")
    empresa_id = data.get("empresaId")
    if not usuario_id or not empresa_id:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    usuario = cursor.execute("SELECT * FROM usuario WHERE Id = ?", (usuario_id,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404
    if usuario["tipoUsuario"] != "delegado":
        conn.close()
        return jsonify({"error": "El usuario no es delegado"}), 400
    empresa = cursor.execute("SELECT * FROM empresa WHERE empresaid = ?", (empresa_id,)).fetchone()
    if not empresa:
        conn.close()
        return jsonify({"error": "Empresa no encontrada"}), 404
    existe = cursor.execute(
        "SELECT delegadoId FROM delegado WHERE Id = ?", (usuario_id,)
    ).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "El usuario ya es delegado"}), 400
    cursor.execute(
        "INSERT INTO delegado (Id, empresaId) VALUES (?, ?)",
        (usuario_id, empresa_id)
    )
    delegado_id = cursor.lastrowid
    conn.commit()
    new_delegado = cursor.execute("""
        SELECT d.delegadoId, d.Id, d.empresaId, u.nombre, u.correo
        FROM delegado d JOIN usuario u ON d.Id = u.Id
        WHERE d.delegadoId = ?
    """, (delegado_id,)).fetchone()
    conn.close()
    return jsonify(dict(new_delegado)), 201

@app.route("/delegado/<int:delegado_id>", methods=["GET"])
def obtener_delegado(delegado_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    delegado = cursor.execute("""
        SELECT d.delegadoId, d.Id, d.empresaId, u.nombre, u.correo
        FROM delegado d JOIN usuario u ON d.Id = u.Id
        WHERE d.delegadoId = ?
    """, (delegado_id,)).fetchone()
    conn.close()
    if not delegado:
        return jsonify({"error": "Delegado no encontrado"}), 404
    return jsonify(dict(delegado))

# -------------------- CANDIDATOS --------------------
@app.route("/crear-candidato", methods=["POST"])
def crear_candidato():
    data = request.get_json()
    usuario_id = data.get("usuarioId")
    profesion = data.get("profesion")
    if not usuario_id or not profesion:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    usuario = cursor.execute("SELECT * FROM usuario WHERE Id = ?", (usuario_id,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404
    if usuario["tipoUsuario"] != "candidato":
        conn.close()
        return jsonify({"error": "El usuario no es candidato"}), 400
    existe = cursor.execute(
        "SELECT candidatoId FROM candidato WHERE Id = ?", (usuario_id,)
    ).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "El usuario ya es candidato"}), 400
    cursor.execute(
        "INSERT INTO candidato (Id, profesion) VALUES (?, ?)",
        (usuario_id, profesion)
    )
    candidato_id = cursor.lastrowid
    conn.commit()
    new_candidato = cursor.execute("""
        SELECT c.candidatoId, c.Id, c.profesion, u.nombre, u.correo
        FROM candidato c JOIN usuario u ON c.Id = u.Id
        WHERE c.candidatoId = ?
    """, (candidato_id,)).fetchone()
    conn.close()
    return jsonify(dict(new_candidato)), 201

@app.route("/candidato/<int:candidato_id>", methods=["GET"])
def obtener_candidato(candidato_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    candidato = cursor.execute("""
        SELECT c.candidatoId, c.Id, c.profesion, u.nombre, u.correo
        FROM candidato c JOIN usuario u ON c.Id = u.Id
        WHERE c.candidatoId = ?
    """, (candidato_id,)).fetchone()
    conn.close()
    if not candidato:
        return jsonify({"error": "Candidato no encontrado"}), 404
    return jsonify(dict(candidato))

# -------------------- USUARIOS --------------------
@app.route("/usuario/crear", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    nombre = data.get("nombre")
    correo = data.get("correo")
    numero = data.get("numero")
    tipo = data.get("tipoUsuario")
    password = data.get("password")
    if not all([nombre, correo, numero, tipo, password]):
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    existe = cursor.execute("SELECT * FROM usuario WHERE correo = ?", (correo,)).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "El correo ya está registrado"}), 400
    cursor.execute("""
        INSERT INTO usuario (nombre, correo, numero, tipoUsuario, password)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, correo, numero, tipo, password))
    user_id = cursor.lastrowid
    conn.commit()
    new_user = cursor.execute(
        "SELECT Id, nombre, correo, numero, tipoUsuario FROM usuario WHERE Id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(new_user))

@app.route("/actualizar-usuario/<int:id>", methods=["PUT"])
def actualizar_usuario(id):
    data = request.get_json()
    nombre = data.get("nombre")
    correo = data.get("correo")
    numero = data.get("numero")
    tipo = data.get("tipoUsuario")
    password = data.get("password")
    if not all([nombre, correo, numero, tipo, password]):
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuario SET nombre = ?, correo = ?, numero = ?, tipoUsuario = ?, password = ?
        WHERE Id = ?
    """, (nombre, correo, numero, tipo, password, id))
    conn.commit()
    updated = cursor.execute(
        "SELECT Id, nombre, correo, numero, tipoUsuario FROM usuario WHERE Id = ?", (id,)
    ).fetchone()
    conn.close()
    if not updated:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(dict(updated))

@app.route("/actualizar-contrasena/<int:id>", methods=["PUT"])
def actualizar_contrasena(id):
    data = request.get_json()
    password = data.get("password")
    if not password:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuario SET password = ? WHERE Id = ?", (password, id))
    conn.commit()
    # Optionally return user info without password
    user = cursor.execute(
        "SELECT Id, nombre, correo, numero, tipoUsuario FROM usuario WHERE Id = ?", (id,)
    ).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(dict(user))

@app.route("/borrar-usuario/<int:id>", methods=["DELETE"])
def borrar_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT Id, nombre, correo, numero, tipoUsuario FROM usuario WHERE Id = ?", (id,)
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404
    user_dict = dict(user)
    cursor.execute("DELETE FROM usuario WHERE Id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify(user_dict)

@app.route("/usuario/<int:id>", methods=["GET"])
def obtener_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    usuario = cursor.execute(
        "SELECT Id, nombre, correo, numero, tipoUsuario FROM usuario WHERE Id = ?", (id,)
    ).fetchone()
    conn.close()
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(dict(usuario))

# -------------------- CANDIDATO - OFERTAS Y POSTULACIONES --------------------
@app.route("/candidato/<int:id>/ofertas", methods=["GET"])
def ver_ofertas_candidato(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM oferta")
    ofertas = cursor.fetchall()
    conn.close()
    if not ofertas:
        return jsonify({"error": "No hay ofertas disponibles"}), 404
    return jsonify([dict(row) for row in ofertas])

@app.route("/candidato/<int:id>/ofertas/<int:oferta_id>/postular", methods=["POST"])
def postular_oferta(id, oferta_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    candidato = cursor.execute(
        "SELECT candidatoId FROM candidato WHERE Id = ?", (id,)
    ).fetchone()
    if not candidato:
        conn.close()
        return jsonify({"error": "Usuario no es candidato"}), 400
    candidato_id = candidato["candidatoId"]
    oferta = cursor.execute(
        "SELECT * FROM oferta WHERE ofertaId = ?", (oferta_id,)
    ).fetchone()
    if not oferta:
        conn.close()
        return jsonify({"error": "Oferta no encontrada"}), 404
    existe_postulacion = cursor.execute(
        "SELECT postulacionId FROM postulacion WHERE candidatoId = ? AND ofertaId = ?",
        (candidato_id, oferta_id)
    ).fetchone()
    if existe_postulacion:
        conn.close()
        return jsonify({"error": "Ya estás postulado a esta oferta"}), 400
    cursor.execute(
        "INSERT INTO postulacion (candidatoId, ofertaId, estadoPostulacion) VALUES (?, ?, 2)",
        (candidato_id, oferta_id)
    )
    postulacion_id = cursor.lastrowid
    conn.commit()
    new_postulacion = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (postulacion_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(new_postulacion))

@app.route("/postulacion/<int:postulacion_id>", methods=["GET"])
def obtener_postulacion(postulacion_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    postulacion = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (postulacion_id,)
    ).fetchone()
    conn.close()
    if not postulacion:
        return jsonify({"error": "Postulación no encontrada"}), 404
    return jsonify(dict(postulacion))

@app.route("/postulacion/<int:postulacion_id>", methods=["DELETE"])
def cancelar_postulacion(postulacion_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    postulacion = cursor.execute(
        "SELECT * FROM postulacion WHERE postulacionId = ?", (postulacion_id,)
    ).fetchone()
    if not postulacion:
        conn.close()
        return jsonify({"error": "Postulación no encontrada"}), 404
    postulacion_dict = dict(postulacion)
    cursor.execute("DELETE FROM postulacion WHERE postulacionId = ?", (postulacion_id,))
    conn.commit()
    conn.close()
    return jsonify(postulacion_dict)

@app.route("/chats/<int:idU>", methods = ["GET"])
def ver_chats(idU):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    nombreU = cursor.execute("SELECT nombre FROM usuario WHERE Id = ?", (idU,)).fetchone()
    if not nombreU:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    chats = obtener_chats_usuario(idU)
    # chats sera una lista de diccionarios
    
    if not chats:
        return jsonify ({"error": "El usuario no tiene chats"}), 404

    resultado = []
    for chat in chats:
        # al hacer la iteracion, obtenemos un chat, es decir, un diccionario simple, esto simplifica bastante la obtencion de datos
        candidatoId = chat.get("id_candidato")
        delegadoId = chat.get("id_delegado")
        nombreDelegado = cursor.execute('''
                        SELECT usuario.nombre FROM usuario JOIN delegado ON usuario.Id = delegado.Id WHERE delegado.delegadoId = ?
                        ''', (delegadoId,)).fetchone()
        nombreCandidato = cursor.execute('''
                        SELECT usuario.nombre FROM usuario JOIN candidato ON usuario.Id = candidato.Id WHERE candidato.candidatoId = ?
                        ''', (candidatoId,)).fetchone()
        
        # Esta fecha sera al del ultimo mensaje enviado
        # Los corchetes son para evitar errores en la iteracion en caso de que no haya mensajes en el chat
        mensajes = chat.get("mensajes", [])
        fecha = None
        for mensaje in mensajes:
            # Para usar la clase datetime, hay que importar la biblioteca datetima
            # strptime es un metodo que nos va a permitir comparar dos fechas
            fecha1 = datetime.strptime(mensaje.get("timestamp"), "%Y-%m-%dT%H:%M:%S")
            if fecha1>fecha or fecha is None:
                fecha = fecha1  
                
        resultado.append({
         "id_chat": chat.get("id_chat"),
         # Se usa un indice al obtener el nombre del delegado y candidato para obtener el formato correcto
         "delegado": nombreDelegado[0] if  nombreDelegado else None,
         "candidato": nombreCandidato[0] if nombreCandidato else None,
         "fecha": fecha.isoformat if fecha else None
        }
        )
             
    return jsonify(resultado)


@app.route("/chats/<int:idU>/<int:idChat>", methods=["GET"])
def obtener_chat(idU, idChat):

    conn = get_db_connection()
    cursor = conn.cursor()
    
    chats = obtener_chats_usuario(idU)
    if not chats:
        return jsonify({"Error": "El usuario no tiene chats"}), 404
    
    chatMongo = ver_chat(idChat)
    if not chatMongo:
        return jsonify({"Error": "No existe dicho chat"}), 404

    idChatB = chatMongo.get("id_chat")
    
    chatB = None
    for n in range(len(chats)):
        if chats[n].get("id_chat") == idChatB:
            chatB = chats[n]
            break

    if not chatB:
        return jsonify({"Error": "El chat no pertenece a este usuario"}), 404
    
    nombreCandidato = cursor.execute('''
        SELECT usuario.nombre FROM usuario 
        JOIN candidato ON usuario.Id = candidato.Id 
        WHERE candidato.candidatoId = ?
    ''', (chatB.get("id_candidato"),)).fetchone()

    nombreDelegado = cursor.execute('''
        SELECT usuario.nombre FROM usuario 
        JOIN delegado ON usuario.Id = delegado.Id 
        WHERE delegado.delegadoId = ?
    ''', (chatB.get("id_delegado"),)).fetchone()

    mensajes = chatB.get("mensajes", [])

    if not mensajes:
        return jsonify({
            "Candidato": nombreCandidato[0] if nombreCandidato else None,
            "Delegado": nombreDelegado[0] if nombreDelegado else None,
            "Mensajes": "No hay mensajes en este chat aun"
        })
    
    infoMensaje = []

    for mensaje in mensajes:
        idEmisor = mensaje.get("id_emisor")

        nombreEmisor = (
            nombreCandidato[0] if idEmisor == chatB.get("id_candidato")
            else nombreDelegado[0]
        )

        timestamp = mensaje.get("timestamp")
        fecha = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S") if timestamp else None

        infoMensaje.append({
            "Enviado por": nombreEmisor,
            "Fecha": fecha.isoformat() if fecha else None,
            "Contenido": mensaje.get("contenido")
        })
        
    return jsonify({
        "Candidato": nombreCandidato[0] if nombreCandidato else None,
        "Delegado": nombreDelegado[0] if nombreDelegado else None,
        "Mensajes": infoMensaje
    })
    
    
if __name__ == "__main__":
    app.run(debug=True)