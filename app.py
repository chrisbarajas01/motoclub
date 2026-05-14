# app.py

from flask import Flask, jsonify, request, render_template
import json
import os
import random
import smtplib
import urllib.parse
import urllib.request
import unicodedata
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask_cors import CORS 

app = Flask(__name__)
# CORS es crucial para que el frontend (en otro dominio de Render) pueda hablar con este backend.
CORS(app) 

# reCAPTCHA keys: cambia estos valores o configúralos en variables de entorno.
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeMxeIsAAAAABVGu_f_1NPeM2KOVCT6BwbFHZ-4')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeMxeIsAAAAAOfJLqZbOgPDRRzZ8XxyehMA9rvG')
RECAPTCHA_DISABLED = os.environ.get('DISABLE_RECAPTCHA', 'false').lower() in ('1', 'true', 'yes')

# =========================================================================
# BASES DE DATOS FALSAS (EN MEMORIA)
# =========================================================================

USUARIOS = {

    "admin@motopower.com": {
        "password": "password123",
        "role": "admin",
        "carrito": [],
        "verified": True
    }
}

LOGIN_CODES = {}

    

INVENTARIO = [
    {"id": 1, "modelo": "Z900", "marca": "Kawasaki", "cilindraje": "948 cc", "disponibles": 5, "precio": 259900, "tipo": "deportiva"},
    {"id": 2, "modelo": "CB650R", "marca": "Honda", "cilindraje": "649 cc", "disponibles": 3, "precio": 214500, "tipo": "deportiva"},
    {"id": 3, "modelo": "R15 V4", "marca": "Yamaha", "cilindraje": "155 cc", "disponibles": 8, "precio": 105000, "tipo": "economica"},
]

EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'TU_CORREO@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'TU_PASSWORD_APP')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))


def generar_codigo_verificacion():
    return str(random.randint(100000, 999999))


def enviar_correo_verificacion(destinatario, codigo):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise RuntimeError('No hay credenciales SMTP configuradas.')

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Verificación de cuenta MotoPower'
    mensaje['From'] = EMAIL_SENDER
    mensaje['To'] = destinatario
    mensaje.set_content(
        f"""Hola,

Gracias por registrarte en MotoPower.

Tu código de verificación es: {codigo}

Ingresa este código en la aplicación para activar tu cuenta.

Si no solicitaste este registro, ignora este mensaje.

Saludos,
MotoPower
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(mensaje)


def crear_usuario_no_verificado(email, password):
    codigo = generar_codigo_verificacion()
    USUARIOS[email] = {
        'password': password,
        'role': 'user',
        'carrito': [],
        'verified': False,
        'verification_code': codigo
    }
    return codigo


def guardar_codigo_login(email):
    codigo = generar_codigo_verificacion()
    expiracion = datetime.utcnow() + timedelta(minutes=10)
    LOGIN_CODES[email] = {
        'code': codigo,
        'expires_at': expiracion
    }
    return codigo


def enviar_correo_codigo_login(destinatario, codigo):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise RuntimeError('No hay credenciales SMTP configuradas.')

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Código temporal de acceso MotoPower'
    mensaje['From'] = EMAIL_SENDER
    mensaje['To'] = destinatario
    mensaje.set_content(
        f"""Hola,

Has solicitado iniciar sesión en MotoPower.

Tu código temporal de acceso es: {codigo}

Este código es válido por 10 minutos.

Si no fuiste tú, ignora este mensaje.

Saludos,
MotoPower
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(mensaje)



def validar_codigo_login(email, codigo):
    if not email or not codigo:
        return False

    datos = LOGIN_CODES.get(email)
    if not datos:
        return False

    if datos.get('expires_at') < datetime.utcnow():
        LOGIN_CODES.pop(email, None)
        return False

    if str(datos.get('code')) != str(codigo).strip():
        return False

    LOGIN_CODES.pop(email, None)
    return True

# ==========================================================
# CHATBOT
# ==========================================================

def limpiar_texto(texto):
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto


def detectar_intencion(msg):
    if any(x in msg for x in ["hola", "buenas", "hey", "hello", "hi"]):
        return "saludo"
    elif any(x in msg for x in ["catalogo", "catálogo", "ver motos", "inventario"]):
        return "catalogo"
    elif any(x in msg for x in ["ayuda", "help", "no entiendo"]):
        return "ayuda"
    elif any(x in msg for x in ["ubicacion", "direccion", "donde estan"]):
        return "ubicacion"
    elif any(x in msg for x in ["envio", "delivery"]):
        return "envios"
    elif any(x in msg for x in ["garantia", "devolucion"]):
        return "devoluciones"
    elif any(x in msg for x in ["pago", "tarjeta", "transferencia"]):
        return "pagos"
    elif any(x in msg for x in ["promocion", "descuento"]):
        return "promociones"
    elif any(x in msg for x in ["gracias", "bye", "adios"]):
        return "despedida"
    elif any(x in msg for x in ["comprar", "quiero", "busco"]):
        return "compra"
    return "otro"


def filtrar_motos(tipo=None, marca=None, presupuesto=None):
    resultados = INVENTARIO
    if tipo:
        resultados = [m for m in resultados if m.get("tipo") == tipo]
    if marca:
        resultados = [m for m in resultados if marca in m.get("marca", "").lower()]
    if presupuesto:
        resultados = [m for m in resultados if m.get("precio", 0) <= presupuesto]
    return resultados


def mostrar_motos(lista):
    if not lista:
        return "😅 No encontré motos con esas características."
    texto = "🏍️ Opciones disponibles:\n"
    for m in lista:
        texto += f"- {m['marca']} {m['modelo']} (${m['precio']})\n"
    return texto


def responder(msg):
    intent = detectar_intencion(msg)
    palabras = msg.split()
    presupuesto = None
    for p in palabras:
        if p.isdigit():
            presupuesto = int(p)
    marca = None
    for m in ["yamaha", "honda", "italika", "kawasaki"]:
        if m in msg:
            marca = m
    tipo = None
    if "economica" in msg or "barata" in msg:
        tipo = "economica"
    elif "deportiva" in msg:
        tipo = "deportiva"
    elif "trabajo" in msg:
        tipo = "trabajo"
    if tipo or marca or presupuesto:
        motos = filtrar_motos(
            tipo=tipo,
            marca=marca,
            presupuesto=presupuesto
        )
        return mostrar_motos(motos)
    if intent == "saludo":
        return "¡Hola! 🏍️ ¿Qué tipo de moto buscas?"
    elif intent == "catalogo":
        return mostrar_motos(INVENTARIO)
    elif intent == "ayuda":
        return (
            "😎 Puedo ayudarte a encontrar motos.\n\n"
            "Ejemplos:\n"
            "- moto barata\n"
            "- yamaha deportiva\n"
            "- moto de trabajo\n"
            "- tengo 50000"
        )
    elif intent == "ubicacion":
        return "📍 Estamos en CDMX."
    elif intent == "envios":
        return "🚚 Hacemos envíos a todo México."
    elif intent == "devoluciones":
        return "🔄 Todas las motos tienen garantía."
    elif intent == "pagos":
        return "💳 Aceptamos efectivo, transferencia y tarjeta."
    elif intent == "promociones":
        return "🔥 Tenemos descuentos y meses sin intereses."
    elif intent == "despedida":
        return "🙌 ¡Gracias por visitarnos!"
    elif intent == "compra":
        return "😎 ¿Qué tipo de moto buscas?"
    else:
        return (
            "🤔 No entendí.\n\n"
            "Puedes escribir:\n"
            "- moto barata\n"
            "- yamaha\n"
            "- deportiva\n"
            "- catálogo"
        )


def chat_response(message):
    return responder(message)

@app.route('/api/chat', methods=['POST'])
def chat():
    datos = request.get_json(silent=True) or {}
    mensaje = datos.get('message', '')
    if not mensaje or not isinstance(mensaje, str):
        return jsonify({'response': 'Escribe tu pregunta para ayudarte con las motos.'})
    respuesta = chat_response(limpiar_texto(mensaje))
    return jsonify({'response': respuesta})


def es_admin(request):
    role = request.headers.get("X-User-Role")
    return role == "admin"

MENSAJES = []

def verificar_recaptcha(token, remote_ip=None):
    if RECAPTCHA_DISABLED:
        return True

    if not token or RECAPTCHA_SECRET_KEY == 'TU_SECRET_KEY_AQUI':
        return False

    data = urllib.parse.urlencode({
        'secret': RECAPTCHA_SECRET_KEY,
        'response': token,
        'remoteip': remote_ip or ''
    }).encode('utf-8')

    request_url = 'https://www.google.com/recaptcha/api/siteverify'
    req = urllib.request.Request(request_url, data=data)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resultado = json.load(resp)
            return resultado.get('success', False)
    except Exception:
        return False

# =========================================================================
# ENDPOINTS DE LA API
# =========================================================================

@app.route('/api/register', methods=['POST'])
def register_usuario():
    """Simula el registro de un nuevo usuario con manejo de errores de JSON."""
    
    # PUNTO DE CORRECCIÓN: Intentamos obtener el JSON con manejo de errores
    try:
        datos_registro = request.get_json()
    except Exception:
        # Si la petición no es JSON válido (cuerpo vacío o mal formato)
        return jsonify({"mensaje": "Error en la petición: Asegúrate de que estás enviando JSON válido."}), 400
    
    # Manejar el caso donde get_json() devuelve None (Ej. content-type incorrecto o cuerpo vacío)
    if not datos_registro:
        return jsonify({"mensaje": "Error: El cuerpo de la petición está vacío o no es JSON."}), 400
        
    if 'email' not in datos_registro or 'password' not in datos_registro:
        return jsonify({"mensaje": "Email y contraseña son requeridos para el registro."}), 400

    recaptcha_token = datos_registro.get('recaptchaToken')
    if not recaptcha_token:
        return jsonify({"mensaje": "Por favor completa el CAPTCHA."}), 400

    if not verificar_recaptcha(recaptcha_token, request.remote_addr):
        return jsonify({"mensaje": "Validación de reCAPTCHA fallida. Intenta de nuevo."}), 400
    
    email = datos_registro['email'].strip().lower()
    password = datos_registro['password']

    # 1. Verificar si el usuario ya existe
    if email in USUARIOS:
        if USUARIOS[email].get('verified'):
            return jsonify({"mensaje": f"El email {email} ya está registrado."}), 409
        return jsonify({"mensaje": "El email ya está registrado. Revisa tu correo para verificar la cuenta."}), 409

    # 2. Guardar el usuario como no verificado y enviar código
    codigo = crear_usuario_no_verificado(email, password)

    try:
        enviar_correo_verificacion(email, codigo)
    except Exception as error:
        USUARIOS.pop(email, None)
        return jsonify({
            "mensaje": "No se pudo enviar el correo de verificación. Revisa la configuración de Gmail.",
            "error": str(error)
        }), 500

    return jsonify({
        "mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."
    }), 201


@app.route('/api/verify-email', methods=['POST'])
def verificar_email():
    try:
        datos_verificacion = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición: Asegúrate de que estás enviando JSON válido."}), 400

    if not datos_verificacion or 'email' not in datos_verificacion or 'code' not in datos_verificacion:
        return jsonify({"mensaje": "Correo y código de verificación son requeridos."}), 400

    email = datos_verificacion['email'].strip().lower()
    codigo = str(datos_verificacion['code']).strip()

    if email not in USUARIOS:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    if USUARIOS[email].get('verified'):
        return jsonify({"mensaje": "La cuenta ya está verificada."}), 200

    if USUARIOS[email].get('verification_code') != codigo:
        return jsonify({"mensaje": "Código de verificación incorrecto."}), 400

    USUARIOS[email]['verified'] = True
    USUARIOS[email].pop('verification_code', None)

    return jsonify({"mensaje": "Cuenta verificada. Ya puedes iniciar sesión."}), 200


@app.route('/api/resend-verification', methods=['POST'])
def reenviar_verificacion():
    try:
        datos_resend = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición: Asegúrate de que estás enviando JSON válido."}), 400

    if not datos_resend or 'email' not in datos_resend:
        return jsonify({"mensaje": "Correo es requerido."}), 400

    email = datos_resend['email'].strip().lower()

    if email not in USUARIOS:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    if USUARIOS[email].get('verified'):
        return jsonify({"mensaje": "La cuenta ya está verificada."}), 200

    codigo = generar_codigo_verificacion()
    USUARIOS[email]['verification_code'] = codigo

    try:
        enviar_correo_verificacion(email, codigo)
    except Exception as error:
        return jsonify({
            "mensaje": "No se pudo reenviar el correo de verificación.",
            "error": str(error)
        }), 500

    return jsonify({"mensaje": "Código de verificación reenviado. Revisa tu correo."}), 200


@app.route('/api/login', methods=['POST'])
def login_usuario():
    try:
        datos_login = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición"}), 400
        
    if not datos_login or 'email' not in datos_login or 'password' not in datos_login:
        return jsonify({"mensaje": "Email y contraseña son requeridos"}), 400

    recaptcha_token = datos_login.get('recaptchaToken')
    if not recaptcha_token:
        return jsonify({"mensaje": "Por favor completa el CAPTCHA."}), 400

    if not verificar_recaptcha(recaptcha_token, request.remote_addr):
        return jsonify({"mensaje": "Validación de reCAPTCHA fallida. Intenta de nuevo."}), 400
    
    email = datos_login['email'].strip().lower()
    password = datos_login['password']
    
    if email not in USUARIOS or USUARIOS[email]["password"] != password:
        return jsonify({"mensaje": "Credenciales inválidas"}), 401

    if not USUARIOS[email].get('verified'):
        return jsonify({"mensaje": "Cuenta no verificada. Revisa tu correo para completar el registro."}), 403

    role = USUARIOS[email]["role"]

    try:
        codigo = guardar_codigo_login(email)
        enviar_correo_codigo_login(email, codigo)
    except Exception as error:
        return jsonify({"mensaje": "No se pudo enviar el código de acceso temporal.", "error": str(error)}), 500

    return jsonify({
        "mensaje": "Se envió un código temporal a tu correo. Ingresa el código para completar el inicio de sesión.",
        "requiresVerification": True,
        "usuario": email,
        "role": role
    }), 200


@app.route('/api/login-verify-code', methods=['POST'])
def verificar_login_codigo():
    try:
        datos = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición: Asegúrate de que estás enviando JSON válido."}), 400

    if not datos or 'email' not in datos or 'code' not in datos:
        return jsonify({"mensaje": "Email y código son requeridos."}), 400

    email = datos['email'].strip().lower()
    codigo = str(datos['code']).strip()

    if email not in USUARIOS:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    if not validar_codigo_login(email, codigo):
        return jsonify({"mensaje": "Código de acceso inválido o caducado."}), 400

    role = USUARIOS[email]["role"]
    return jsonify({
        "mensaje": "Inicio de sesión exitoso",
        "token": f"fake_jwt_{email}_hash",
        "usuario": email,
        "role": role
    }), 200


@app.route('/api/login-resend-code', methods=['POST'])
def reenviar_codigo_login():
    try:
        datos = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición: Asegúrate de que estás enviando JSON válido."}), 400

    if not datos or 'email' not in datos:
        return jsonify({"mensaje": "Email es requerido."}), 400

    email = datos['email'].strip().lower()

    if email not in USUARIOS:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    try:
        codigo = guardar_codigo_login(email)
        enviar_correo_codigo_login(email, codigo)
    except Exception as error:
        return jsonify({"mensaje": "No se pudo reenviar el código de acceso.", "error": str(error)}), 500

    return jsonify({"mensaje": "Código temporal reenviado a tu correo."}), 200


@app.route('/api/inventario', methods=['GET'])
def obtener_inventario():
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    return jsonify(INVENTARIO)

@app.route('/api/inventario', methods=['POST'])
def crear_moto():
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    data = request.get_json()
    nuevo_id = max(m["id"] for m in INVENTARIO) + 1

    nueva_moto = {
        "id": nuevo_id,
        "modelo": data["modelo"],
        "marca": data["marca"],
        "cilindraje": data["cilindraje"],
        "disponibles": data["disponibles"],
        "precio": data["precio"]
    }

    INVENTARIO.append(nueva_moto)
    return jsonify(nueva_moto), 201



@app.route('/api/inventario/<int:id>', methods=['PUT'])
def editar_moto(id):
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    data = request.get_json()

    for moto in INVENTARIO:
        if moto["id"] == id:
            moto.update(data)
            return jsonify(moto)

    return jsonify({"mensaje": "Moto no encontrada"}), 404


@app.route('/api/inventario/<int:id>', methods=['DELETE'])
def eliminar_moto(id):
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    global INVENTARIO
    INVENTARIO = [m for m in INVENTARIO if m["id"] != id]
    return jsonify({"mensaje": "Moto eliminada"})

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    lista_usuarios = []

    for email, data in USUARIOS.items():
     lista_usuarios.append({
        "email": email,
        "role": data["role"]
    })


    return jsonify(lista_usuarios)


@app.route('/api/usuarios', methods=['POST'])
def crear_usuario():
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if email in USUARIOS:
        return jsonify({"mensaje": "Usuario ya existe"}), 409

    USUARIOS[email] = {
        "password": password,
        "role": role,
        "carrito": []
    }

    return jsonify({"mensaje": "Usuario creado"}), 201

@app.route('/api/usuarios/<email>', methods=['PUT'])
def editar_usuario(email):
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    if email not in USUARIOS:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    data = request.get_json()
    USUARIOS[email]["role"] = data.get("role", "user")

    return jsonify({"mensaje": "Usuario actualizado"})

@app.route('/api/usuarios/<email>', methods=['DELETE'])
def eliminar_usuario(email):
    if not es_admin(request):
        return jsonify({"mensaje": "Acceso denegado"}), 403

    if email == "admin@motopower.com":
        return jsonify({"mensaje": "No puedes eliminar al admin"}), 400

    USUARIOS.pop(email, None)
    return jsonify({"mensaje": "Usuario eliminado"})



@app.route('/api/contacto', methods=['POST'])
def recibir_contacto():
    """Recibe los datos del formulario de contacto."""
    
    # Implementamos el mismo try/except para contacto
    try:
        datos_contacto = request.get_json()
    except Exception:
        return jsonify({"mensaje": "Error en la petición: El cuerpo de la solicitud no es JSON válido."}), 400
    
    if not datos_contacto or 'nombre' not in datos_contacto or 'correo' not in datos_contacto or 'mensaje' not in datos_contacto:
        return jsonify({"mensaje": "Datos incompletos"}), 400
    
    MENSAJES.append(datos_contacto)
    
    return jsonify({"mensaje": "¡Gracias! Hemos recibido tu mensaje."}), 201


@app.route('/api/carrito', methods=['GET'])
def obtener_carrito():
    email = request.headers.get("X-User-Email")

    if not email or email not in USUARIOS:
        return jsonify({"mensaje": "No autorizado"}), 401

    return jsonify(USUARIOS[email]["carrito"])


@app.route('/api/carrito', methods=['POST'])
def agregar_carrito():
    email = request.headers.get("X-User-Email")
    data = request.get_json()

    if not email or email not in USUARIOS:
        return jsonify({"mensaje": "No autorizado"}), 401

    USUARIOS[email]["carrito"].append(data)
    return jsonify({"mensaje": "Producto agregado"})

@app.route('/api/carrito', methods=['DELETE'])
def vaciar_carrito():
    email = request.headers.get("X-User-Email")

    if not email or email not in USUARIOS:
        return jsonify({"mensaje": "No autorizado"}), 401

    USUARIOS[email]["carrito"] = []
    return jsonify({"mensaje": "Carrito vacío"})


@app.route('/')
def index():
    return render_template('index.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)
# =========================================================================
# INICIO DEL SERVIDOR
# =========================================================================
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404


if __name__ == '__main__':
    # Usar host 0.0.0.0 y puerto 5000 para despliegue y pruebas locales
    app.run(host='0.0.0.0', port=5000, debug=True)


    
