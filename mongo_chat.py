from pymongo import MongoClient

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

def crear_chat(data):
    chats.insert_one(data)
    
def enviar_mensaje(id_chat, mensaje):
    chats.update_one(
        {"id_chat": id_chat},
        {"$push": {"mensajes": mensaje}}
    )