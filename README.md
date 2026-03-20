ProLink API

ProLink es una API desarrollada con Flask y SQLite para la gestión de un sistema de reclutamiento laboral. Permite administrar usuarios, empresas, ofertas de trabajo y postulaciones, diferenciando entre roles como delegados y candidatos.

Descripción

El sistema está diseñado para:

Gestionar usuarios con distintos roles (delegado y candidato)

Permitir a los delegados crear y administrar ofertas laborales

Permitir a los candidatos visualizar ofertas y postularse

Gestionar el ciclo completo de postulaciones (aceptación y rechazo)

Tecnologías utilizadas

Python 3

Flask

SQLite

Flask-CORS

Estructura del proyecto
ProLink/
│── app.py
│── ProLink.db
│── templates/
│   ├── delegado.html
│   └── candidato.html
│── README.md
Instalación

Clonar el repositorio:

git clone https://github.com/tu-usuario/prolink.git
cd prolink

Crear entorno virtual (opcional):

python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

Instalar dependencias:

pip install flask flask-cors
Ejecución
python app.py

Servidor disponible en:

http://localhost:5000
Autenticación
POST /login

Soporta solicitudes en formato JSON y formulario.

Ejemplo con JSON:

{
  "correo": "usuario@email.com",
  "password": "123456"
}

Respuesta:

{
  "message": "Login exitoso",
  "id": 1,
  "tipoUsuario": "delegado"
}
Endpoints principales
Usuarios

POST /usuario/crear

GET /usuario/<id>

PUT /actualizar-usuario/<id>

PUT /actualizar-contrasena/<id>

DELETE /borrar-usuario/<id>

Empresas

POST /delegado/<id>/empresa

GET /delegado/<id>/empresa/<empresaid>

PUT /delegado/<id>/empresa/<empresaid>

DELETE /delegado/<id>/empresa/<empresaid>

Ofertas

GET /delegado/<id>/oferta

GET /delegado/<id>/oferta/<ofertaId>

POST /delegado/<id>/oferta/crear

PUT /delegado/<id>/oferta/<ofertaId>

DELETE /delegado/<id>/oferta/<ofertaId>

Postulaciones

GET /delegado/<id>/oferta/<ofertaId>/postulacion

PUT /delegado/<id>/oferta/<ofertaId>/postulacion/<idPostulacion>/aceptar

PUT /delegado/<id>/oferta/<ofertaId>/postulacion/<idPostulacion>/rechazar

POST /candidato/<id>/ofertas/<ofertaId>/postular

GET /postulacion/<id>

DELETE /postulacion/<id>

Delegados

POST /crear-delegado

GET /delegado/<id>

Candidatos

POST /crear-candidato

GET /candidato/<id>

GET /candidato/<id>/ofertas

Consideraciones

Las contraseñas se almacenan actualmente en texto plano.

No se utiliza autenticación basada en tokens.

El proyecto está orientado a aprendizaje o prototipos.

Mejoras futuras

Implementar hashing de contraseñas

Agregar autenticación con JWT

Separar el proyecto en capas (routes, services, models)

Implementar pruebas automatizadas

Preparar despliegue en producción

Autor

Proyecto desarrollado como práctica de backend con Flask.

Licencia

Uso libre con fines educativos.
