# 📧 Configuración de Email para ARC Manager

Esta guía te ayudará a configurar el sistema de correo electrónico para tu aplicación ARC Manager. Hemos incluido múltiples opciones, desde servicios gratuitos para testing hasta soluciones profesionales para producción.

## 🚀 Opciones Recomendadas (Sin Dominio Propio)

### 1. SendGrid (⭐ RECOMENDADO PARA TESTING)

**Ventajas:**
- ✅ 100 emails/día GRATIS para siempre
- ✅ Acepta Gmail, Yahoo, etc. para registro
- ✅ Excelente deliverability
- ✅ Fácil configuración con Django
- ✅ Dashboard completo con estadísticas

**Configuración para Railway:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=[tu_api_key_de_sendgrid]
DEFAULT_FROM_EMAIL=tu_email@gmail.com
```

**Pasos para configurar SendGrid:**
1. Regístrate en [SendGrid](https://sendgrid.com)
2. Verifica tu cuenta de email
3. Ve a Settings → API Keys
4. Crea una nueva API Key con permisos de "Mail Send"
5. Copia la API Key y úsala como `EMAIL_HOST_PASSWORD`

### 2. Brevo (ex-Sendinblue)

**Ventajas:**
- ✅ 300 emails/día GRATIS
- ✅ Acepta correos personales
- ✅ Interfaz muy intuitiva

**Configuración:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.sendinblue.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_smtp_key_brevo
DEFAULT_FROM_EMAIL=tu_email@gmail.com
```

### 3. Mailgun

**Ventajas:**
- ✅ 5,000 emails/mes gratis los primeros 3 meses
- ✅ Muy popular entre desarrolladores
- ⚠️ Después baja a plan de pago

**Configuración:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@tu-dominio-mailgun.com
EMAIL_HOST_PASSWORD=tu_password_mailgun
DEFAULT_FROM_EMAIL=noreply@tu-dominio-mailgun.com
```

### 4. Gmail SMTP (Para testing rápido)

**Ventajas:**
- ✅ Configuración muy rápida
- ✅ Ideal para desarrollo local
- ⚠️ Requiere activar "App Passwords" en Gmail

**Configuración:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_gmail
DEFAULT_FROM_EMAIL=tu_email@gmail.com
```

**Pasos para Gmail:**
1. Activa la verificación en 2 pasos en tu cuenta de Google
2. Ve a Configuración de la cuenta → Seguridad → Contraseñas de aplicaciones
3. Genera una contraseña de aplicación para "Mail"
4. Usa esa contraseña como `EMAIL_HOST_PASSWORD`

## 🏭 Para Producción con Dominio Propio

### SMTP2GO
- ✅ 1,000 emails/mes gratis
- ✅ Excelente para producción
- ✅ Soporte técnico profesional

### Amazon SES
- ✅ Muy económico para grandes volúmenes
- ✅ Integración completa con AWS
- ⚠️ Requiere configuración más compleja

## 🔧 Configuración en Railway

1. Ve a tu proyecto en Railway
2. Accede a la pestaña "Variables"
3. Agrega las variables de entorno según el proveedor elegido
4. Reinicia el deployment

## 🧪 Pruebas de Email

Para probar que el email funciona correctamente:

1. **En desarrollo local:**
   ```bash
   python manage.py shell
   from django.core.mail import send_mail
   send_mail('Prueba', 'Mensaje de prueba', 'from@example.com', ['to@example.com'])
   ```

2. **Usar la funcionalidad de reset de password:**
   - Ve a la página de login
   - Haz clic en "¿Olvidaste tu contraseña?"
   - Introduce un email válido
   - Verifica que llegue el correo

## 💡 Recomendaciones

1. **Para testing/desarrollo:** Usa SendGrid
2. **Para producción pequeña:** Mantén SendGrid o migra a SMTP2GO
3. **Para producción grande:** Considera Amazon SES
4. **Para desarrollo local:** Gmail SMTP es la opción más rápida

## 🔒 Consideraciones de Seguridad

- Nunca hardcodees las credenciales en el código
- Usa variables de entorno en Railway
- Mantén las API keys seguras
- Configura SPF/DKIM cuando tengas dominio propio

## 🆘 Troubleshooting

### Error: "SMTPAuthenticationError"
- Verifica que las credenciales sean correctas
- Para Gmail, asegúrate de usar App Password, no tu contraseña normal

### Error: "SMTPRecipientsRefused"
- Verifica que el email de destino sea válido
- Algunos proveedores requieren verificar el dominio remitente

### Emails van a spam
- Configura SPF y DKIM records en tu DNS
- Usa un dominio verificado como remitente
- Evita contenido que parezca spam

## 📊 Monitoreo

Todos los proveedores ofrecen dashboards para monitorear:
- Emails enviados/entregados
- Bounces y rechazos
- Estadísticas de apertura (si está habilitado)

---

**¿Necesitas ayuda?** Revisa los logs de Django en Railway o contacta al soporte del proveedor de email elegido.
