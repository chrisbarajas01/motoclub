#!/usr/bin/env python3
"""
Script para verificar la configuración de variables de entorno
"""
import os

def check_env_vars():
    """Verifica las variables de entorno críticas"""

    print("=== VERIFICACIÓN DE VARIABLES DE ENTORNO ===\n")

    # Variables de email
    email_vars = {
        'EMAIL_SENDER': os.environ.get('EMAIL_SENDER', 'TU_CORREO@gmail.com'),
        'EMAIL_PASSWORD': os.environ.get('EMAIL_PASSWORD', 'TU_PASSWORD_APP'),
        'SMTP_SERVER': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
        'SMTP_PORT': os.environ.get('SMTP_PORT', '587'),
        'DISABLE_EMAIL': os.environ.get('DISABLE_EMAIL', 'false')
    }

    # Variables de reCAPTCHA
    recaptcha_vars = {
        'RECAPTCHA_SITE_KEY': os.environ.get('RECAPTCHA_SITE_KEY', '6LeMxeIsAAAAABVGu_f_1NPeM2KOVCT6BwbFHZ-4'),
        'RECAPTCHA_SECRET_KEY': os.environ.get('RECAPTCHA_SECRET_KEY', '6LeMxeIsAAAAAOfJLqZbOgPDRRzZ8XxyehMA9rvG'),
        'DISABLE_RECAPTCHA': os.environ.get('DISABLE_RECAPTCHA', 'false')
    }

    print("📧 CONFIGURACIÓN DE EMAIL:")
    for var, value in email_vars.items():
        status = "✅" if value != f'TU_{var}' and var != 'DISABLE_EMAIL' else "⚠️"
        if var == 'DISABLE_EMAIL':
            status = "✅" if value.lower() in ('true', '1', 'yes') else "❌"
        elif var == 'EMAIL_PASSWORD' and value == 'TU_PASSWORD_APP':
            status = "⚠️"
        print(f"  {status} {var}: {value}")

    print("\n🤖 CONFIGURACIÓN DE RECAPTCHA:")
    for var, value in recaptcha_vars.items():
        status = "✅" if value != f'6Le{var.split("_")[1]}' and var != 'DISABLE_RECAPTCHA' else "⚠️"
        if var == 'DISABLE_RECAPTCHA':
            status = "✅" if value.lower() in ('true', '1', 'yes') else "❌"
        print(f"  {status} {var}: {value}")

    print("\n📋 RECOMENDACIONES:")
    if email_vars['DISABLE_EMAIL'].lower() not in ('true', '1', 'yes'):
        if email_vars['EMAIL_SENDER'] == 'TU_CORREO@gmail.com':
            print("  ⚠️ Configura EMAIL_SENDER con tu correo real")
        if email_vars['EMAIL_PASSWORD'] == 'TU_PASSWORD_APP':
            print("  ⚠️ Configura EMAIL_PASSWORD con tu app password de Gmail")
        print("  💡 O establece DISABLE_EMAIL=true para desarrollo")

    if recaptcha_vars['DISABLE_RECAPTCHA'].lower() not in ('true', '1', 'yes'):
        print("  ⚠️ Considera DISABLE_RECAPTCHA=true para desarrollo")

    print("\n🎯 ESTADO GENERAL:")
    email_ok = (email_vars['DISABLE_EMAIL'].lower() in ('true', '1', 'yes') or
                (email_vars['EMAIL_SENDER'] != 'TU_CORREO@gmail.com' and
                 email_vars['EMAIL_PASSWORD'] != 'TU_PASSWORD_APP'))

    recaptcha_ok = (recaptcha_vars['DISABLE_RECAPTCHA'].lower() in ('true', '1', 'yes') or
                    recaptcha_vars['RECAPTCHA_SECRET_KEY'] != '6LeMxeIsAAAAAOfJLqZbOgPDRRzZ8XxyehMA9rvG')

    if email_ok and recaptcha_ok:
        print("  ✅ Configuración correcta para desarrollo")
    else:
        print("  ⚠️ Revisa la configuración antes de desplegar")

if __name__ == "__main__":
    check_env_vars()