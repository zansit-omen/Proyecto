import sqlite3
def setup_database():
    try:
        conn = sqlite3.connect("ProLink.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(''' 
                   CREATE TABLE  IF NOT EXISTS usuario 
                   (Id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nombre VARCHAR(100), 
                   correo VARCHAR(50) UNIQUE NOT NULL,
                   numero VARCHAR(10) NOT NULL,
                   tipoUsuario VARCHAR(20),
                   password TEXT NOT NULL
                   );
                   ''')
        cursor.execute(''' 
                   CREATE TABLE  IF NOT EXISTS empresa 
                   ( empresaId INTEGER PRIMARY KEY AUTOINCREMENT,
                   razonSocial VARCHAR (100),
                   correoContacto VARCHAR(50),
                   direccion VARCHAR (50)    
                   );
                   ''')
        cursor.execute('''
                   CREATE TABLE  IF NOT EXISTS delegado 
                   (delegadoId INTEGER PRIMARY KEY AUTOINCREMENT,
                   Id INTEGER NOT NULL REFERENCES usuario(Id) , 
                   empresaId INTEGER REFERENCES empresa(empresaId)                  
                   );
                   ''')
        cursor.execute('''
                   CREATE TABLE  IF NOT EXISTS candidato 
                   (
                    candidatoId INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id INTEGER NOT NULL REFERENCES usuario(Id),
                    profesion VARCHAR(50)
                   );
                   ''')
        cursor.execute('''
                   CREATE TABLE IF NOT EXISTS oferta
                   (
                    ofertaId INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresaId INTEGER NOT NULL REFERENCES empresa(empresaId),
                    titulo VARCHAR (100) NOT NULL,
                    descripcionOferta VARCHAR (500),
                    profesionBuscar VARCHAR (50),
                    estadoOferta INTEGER DEFAULT 1
                   )
                   ''') #Estado de la oferta 1 = abierta, 0 = cerrada
        cursor.execute('''
                   CREATE TABLE  IF NOT EXISTS postulacion
                   (
                    postulacionId INTEGER PRIMARY KEY AUTOINCREMENT,
                    ofertaId INTEGER NOT NULL REFERENCES oferta(ofertaId),
                    candidatoId INTEGER NOT NULL REFERENCES candidato(candidatoId),
                    fechaPostulacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estadoPostulacion INTEGER DEFAULT 2  
                   ) 
                   ''') # Estado postulacion 0 = rechazada, 1 = aceptado, 2 = pendiente 
        seed_data(cursor)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al crear la base de datos {e}")
    
    finally:
        if conn:            
            conn.close()
            
def seed_data(cursor):
    # Delete existing rows (child tables first)
    cursor.execute("DELETE FROM postulacion")
    cursor.execute("DELETE FROM oferta")
    cursor.execute("DELETE FROM candidato")
    cursor.execute("DELETE FROM delegado")
    cursor.execute("DELETE FROM empresa")
    cursor.execute("DELETE FROM usuario")

    cursor.execute("DELETE FROM sqlite_sequence WHERE name='usuario'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='empresa'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='delegado'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='candidato'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='oferta'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='postulacion'")
    # --- Usuarios ---
    cursor.execute('''
        INSERT INTO usuario (nombre, correo, numero, tipoUsuario, password)
        VALUES (?, ?, ?, ?, ?)''',
        ("Juan Perez", "juan@mail.com", "3001111111", "candidato", "JuanPerez123")
    )
    juan_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO usuario (nombre, correo, numero, tipoUsuario, password)
        VALUES (?, ?, ?, ?, ?)''',
        ("Maria Gomez", "maria@mail.com", "3002222222", "candidato", "MariaGomez123")
    )
    maria_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO usuario (nombre, correo, numero, tipoUsuario, password)
        VALUES (?, ?, ?, ?, ?)''',
        ("Carlos Ruiz", "carlos@empresa.com", "3003333333", "delegado", "CarlosRuiz123")
    )
    carlos_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO usuario (nombre, correo, numero, tipoUsuario, password)
        VALUES (?, ?, ?, ?, ?)''',
        ("Ana Torres", "ana@empresa.com", "3004444444", "delegado", "AnaTorres123")
    )
    ana_id = cursor.lastrowid

    # --- Empresas (insert one by one to capture each ID) ---
    cursor.execute('''
        INSERT INTO empresa (razonSocial, correoContacto, direccion)
        VALUES (?, ?, ?)''',
        ("Tech Solutions SAS", "contacto@tech.com", "Bogotá")
    )
    tech_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO empresa (razonSocial, correoContacto, direccion)
        VALUES (?, ?, ?)''',
        ("Innovatech Ltda", "info@innovatech.com", "Medellín")
    )
    innova_id = cursor.lastrowid

    # --- Delegados (use the captured user and company IDs) ---
    cursor.execute('''
        INSERT INTO delegado (Id, empresaId)
        VALUES (?, ?)''',
        (carlos_id, tech_id)
    )
    cursor.execute('''
        INSERT INTO delegado (Id, empresaId)
        VALUES (?, ?)''',
        (ana_id, innova_id)
    )

    # --- Candidatos (use the captured user IDs) ---
    cursor.execute('''
        INSERT INTO candidato (Id, profesion)
        VALUES (?, ?)''',
        (juan_id, "Ingeniero de Software")
    )
    juan_candidato_id = cursor.lastrowid   # capture candidatoId for later use

    cursor.execute('''
        INSERT INTO candidato (Id, profesion)
        VALUES (?, ?)''',
        (maria_id, "Analista de Datos")
    )
    maria_candidato_id = cursor.lastrowid

    # --- Ofertas (use the captured company IDs) ---
    cursor.execute('''
        INSERT INTO oferta (empresaId, titulo, descripcionOferta, profesionBuscar, estadoOferta)
        VALUES (?, ?, ?, ?, ?)''',
        (tech_id, "Backend Developer", "Desarrollador backend con Python", "Ingeniero de Software", 1)
        )
    oferta1_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO oferta (empresaId, titulo, descripcionOferta, profesionBuscar, estadoOferta)
        VALUES (?, ?, ?, ?, ?)''',
        (innova_id, "Data Analyst Jr", "Analista de datos junior", "Analista de Datos", 1)
        )
    oferta2_id = cursor.lastrowid
    
    # --- Postulaciones (use the captured candidato and oferta IDs) ---
    cursor.execute('''
        INSERT INTO postulacion (ofertaId, candidatoId, estadoPostulacion)
        VALUES (?, ?, ?)''',
        (oferta1_id, juan_candidato_id, 0)
    )
    cursor.execute('''
        INSERT INTO postulacion (ofertaId, candidatoId, estadoPostulacion)
        VALUES (?, ?, ?)''',
        (oferta2_id, maria_candidato_id, 0)
    )
    
if __name__=="__main__":
    setup_database()