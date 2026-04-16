from pymongo import MongoClient
from datetime import datetime

#database es la base de datos relacional SQL
database = "ProLink.db"
#DbNoSQL es la base de datos noSQL, client sera la conexion al cluster
#La contraseña del Admin es ProLink123, el cluster se llama ProLink
client = MongoClient("mongodb+srv://Admin:ProLink123@prolink.bcknvo4.mongodb.net/chats_db?appName=ProLink")
# Creacion de la base de datos
DbNoSQL = client["chats_db"]
# Creacion de la coleccion llamada: chats
chats = DbNoSQL["chats"]

# Este metodo ya esta devolviendo una lista de chats, filtrada por el id de usuario
# La lista que retorna es una lista de diccionarios, por lo tanto se tendran que iteraciones para obtener cada diccionario de la lista
def obtener_chats_usuario(idU):
    return list(chats.find({
        "$or": [
            {"id_delegado": idU},
            {"id_candidato": idU}
        ]
    }))

def ver_chat(id_chat):
    return chats.find_one({"id_chat": id_chat})
   
def enviar_mensaje(id_chat, id_emisor, contenido):
    """
    Envía un nuevo mensaje a un chat existente.
    
    Args:
        id_chat: ID del chat
        id_emisor: ID del usuario que envía el mensaje
        contenido: Texto del mensaje
        
    Returns:
        True si se envió correctamente, False si hay error
    """
    
    chat = chats.find_one({"id_chat": id_chat})
    if not chat:
        return False
    
    # Obtener el siguiente id_mensaje
    mensajes = chat.get("mensajes", [])
    id_mensaje = 1 if not mensajes else max([m.get("id_mensaje", 0) for m in mensajes]) + 1
    
    nuevo_mensaje = {
        "id_mensaje": id_mensaje,
        "id_emisor": id_emisor,
        "timestamp": datetime.now().isoformat(),
        "contenido": contenido
    }
    
    chats.update_one(
        {"id_chat": id_chat},
        {"$push": {"mensajes": nuevo_mensaje}}
    )
    return True
    
def eliminar_chat(id_chat):
    chats.delete_one({"id_chat": id_chat})

def eliminar_chat_mensaje(id_chat, idU, id_mensaje):
    """
    Elimina un mensaje específico de un chat.
    Solo el autor del mensaje puede eliminarlo.
    
    Args:
        id_chat: ID del chat
        idU: ID del usuario que intenta eliminar el mensaje
        id_mensaje: ID del mensaje a eliminar
        
    Returns:
        True si se eliminó correctamente, False si hay error
    """
    # Validar que el chat existe
    chat = chats.find_one({"id_chat": id_chat})
    if not chat:
        return False
    
    # Buscar el mensaje en el chat
    mensajes = chat.get("mensajes", [])
    mensaje_encontrado = None
    
    for msg in mensajes:
        if msg.get("id_mensaje") == id_mensaje:
            mensaje_encontrado = msg
            break
    
    # Validar que el mensaje existe
    if not mensaje_encontrado:
        return False
    
    # Validar que el usuario es el autor del mensaje
    if mensaje_encontrado.get("id_emisor") != idU:
        return False
    
    # Eliminar el mensaje usando $pull
    resultado = chats.update_one(
        {"id_chat": id_chat},
        {"$pull": {"mensajes": {"id_mensaje": id_mensaje}}}
    )
    
    return True

def crear_chat_con_mensaje(id_delegado, id_candidato, id_emisor, contenido):
    """
    Crea un nuevo chat entre un delegado y candidato con el primer mensaje.
    
    Args:
        id_delegado: ID del delegado
        id_candidato: ID del candidato
        id_emisor: ID del usuario que envía el primer mensaje (delegado o candidato)
        contenido: Texto del primer mensaje
        
    Returns:
        El chat creado o None si hay error
    """
    from datetime import datetime
    
    # Obtener el siguiente id_chat (max + 1)
    ultimo_chat = list(chats.find().sort("id_chat", -1).limit(1))
    id_chat = 1 if not ultimo_chat else ultimo_chat[0].get("id_chat", 0) + 1
    
    nuevo_chat = {
        "id_chat": id_chat,
        "id_delegado": id_delegado,
        "id_candidato": id_candidato,
        "mensajes": [
            {
                "id_mensaje": 1,
                "id_emisor": id_emisor,
                "timestamp": datetime.now().isoformat(),
                "contenido": contenido
            }
        ]
    }
    
    chats.insert_one(nuevo_chat)
    return nuevo_chat  