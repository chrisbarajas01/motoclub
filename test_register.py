#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del registro
"""
import os
import sys
import json
import requests
from datetime import datetime

# Configurar variables de entorno para pruebas
os.environ['DISABLE_EMAIL'] = 'true'
os.environ['DISABLE_RECAPTCHA'] = 'true'

def test_registration():
    """Prueba el endpoint de registro"""

    # URL del servidor (cambiar según corresponda)
    base_url = "http://localhost:5000"  # Para pruebas locales
    # base_url = "https://tu-app-en-render.com"  # Para pruebas en Render

    test_data = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "testpassword123",
        "recaptchaToken": "test_token"  # No se valida cuando está deshabilitado
    }

    try:
        print(f"Probando registro con email: {test_data['email']}")
        print(f"URL: {base_url}/api/register")

        response = requests.post(
            f"{base_url}/api/register",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 201:
            print("✅ Registro exitoso")
            return True
        else:
            print("❌ Error en registro")
            return False

    except requests.exceptions.Timeout:
        print("❌ Timeout en la petición")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    print("=== PRUEBA DE REGISTRO ===")
    print(f"DISABLE_EMAIL: {os.environ.get('DISABLE_EMAIL', 'false')}")
    print(f"DISABLE_RECAPTCHA: {os.environ.get('DISABLE_RECAPTCHA', 'false')}")
    print()

    success = test_registration()

    if success:
        print("\n✅ La prueba fue exitosa")
        sys.exit(0)
    else:
        print("\n❌ La prueba falló")
        sys.exit(1)