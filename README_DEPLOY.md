# 🚀 Guía de Despliegue en Render

## Problema Resuelto
El registro se quedaba cargando en Render porque faltaban las variables de entorno para el envío de emails.

## ✅ Solución Implementada
- **Modo desarrollo**: Variable `DISABLE_EMAIL=true` para pruebas sin envío real
- **Timeouts**: 10 segundos máximo para envío de emails
- **Mejor manejo de errores**: Mensajes específicos en lugar de timeouts infinitos

## 🔧 Variables de Entorno Requeridas en Render

Ve a tu dashboard de Render → Environment y configura:

### Para Desarrollo/Pruebas (recomendado inicialmente):
```
DISABLE_EMAIL=true
DISABLE_RECAPTCHA=true
```

### Para Producción (cuando tengas email configurado):
```
EMAIL_SENDER=tu_correo@gmail.com
EMAIL_PASSWORD=tu_password_app_de_gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
RECAPTCHA_SITE_KEY=tu_site_key
RECAPTCHA_SECRET_KEY=tu_secret_key
```

## 📧 Configuración de Gmail

1. Ve a [Google Account Settings](https://myaccount.google.com/)
2. Activa la verificación en 2 pasos
3. Genera una "App Password":
   - Ve a Security → 2-Step Verification → App passwords
   - Selecciona "Mail" y "Other (custom name)"
   - Copia la contraseña de 16 caracteres
4. Usa esa contraseña (no tu contraseña normal) en `EMAIL_PASSWORD`

## 🧪 Probar Localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pruebas
python test_register.py

# Ejecutar servidor
python app.py
```

## 🚀 Desplegar en Render

1. **Sube los cambios** a tu repositorio Git
2. **Redeploy** en Render
3. **Verifica logs** para confirmar que funciona

## 🔍 Debugging

Si sigue fallando:
1. Revisa los logs de Render
2. Verifica que las variables de entorno estén configuradas
3. Prueba con `DISABLE_EMAIL=true` primero
4. Usa el script `test_register.py` para probar localmente

## 📝 Notas Importantes

- Los usuarios se almacenan en memoria (se pierden al reiniciar)
- Para producción real, necesitarás una base de datos persistente
- El reCAPTCHA puede estar deshabilitado para desarrollo