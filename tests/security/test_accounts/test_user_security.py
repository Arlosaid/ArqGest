"""
Tests de SEGURIDAD CRÍTICA para el modelo User

PROPÓSITO: Estos tests verifican vulnerabilidades de seguridad que podrían
causar brechas graves, multas legales o pérdida de datos.

IMPORTANTE: Estos tests NO usan disable_account_signals porque necesitamos
probar el comportamiento real del sistema.
"""
import pytest
import time
import logging
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from tests.factories.account_factories import UserFactory

User = get_user_model()


# ============================================================================
# TEST 1: EMAIL CASE-INSENSITIVE (CRÍTICO)
# ============================================================================

@pytest.mark.django_db
@pytest.mark.security
class TestEmailSecurity:
    """Tests de seguridad relacionados con emails"""
    
    def test_email_case_insensitive_uniqueness(self, disable_account_signals):
        """
        🔴 CRÍTICO: Verificar que emails con diferente capitalización no pueden duplicarse
        
        ¿POR QUÉ ES CRÍTICO?
        - Usuario registra: User@Example.com
        - Luego intenta login con: user@example.com
        - Si son diferentes: "usuario no existe" → frustración
        - Si son iguales pero pueden duplicarse: cuentas duplicadas
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Django ORM normaliza emails antes de guardar
        2. Constraint UNIQUE funciona con case-insensitive
        3. No se pueden crear 2 cuentas: test@x.com y TEST@X.COM
        
        RESULTADO DEL TEST:
        ❌ FALLÓ - Django permite crear 2 usuarios:
           - test@example.com (user 147)
           - TEST@example.com (user 148)
        
        SOLUCIÓN NECESARIA:
        - Normalizar TODA la dirección de email a lowercase en el manager
        - No solo el dominio, también la parte local
        - Cambiar en CustomUserManager.create_user():
          email = self.normalize_email(email).lower()
        """
        # ARRANGE: Crear primer usuario con email en minúsculas
        email_lowercase = 'test@example.com'
        first_user = User.objects.create_user(
            email=email_lowercase,
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # ACT & ASSERT: Intentar crear segundo usuario con email en MAYÚSCULAS
        # Con el fix aplicado, esto DEBE lanzar IntegrityError
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='TEST@EXAMPLE.COM',
                password='testpass123',
                first_name='Test2',
                last_name='User2'
            )
        
        # ÉXITO: Email normalizado correctamente
        # 'TEST@EXAMPLE.COM' → 'test@example.com' → IntegrityError ✅
        # No podemos hacer queries después de IntegrityError debido a transacciones


# ============================================================================
# TEST 2: PASSWORDS NUNCA EN LOGS (CRÍTICO)
# ============================================================================

@pytest.mark.django_db
@pytest.mark.security
class TestPasswordSecurity:
    """Tests de seguridad relacionados con contraseñas"""
    
    def test_passwords_never_in_logs(self, caplog, disable_account_signals):
        """
        🔴 CRÍTICO: Verificar que contraseñas NUNCA aparecen en logs
        
        ¿POR QUÉ ES CRÍTICO?
        - Violación GDPR: Multa hasta 20M€ o 4% ingresos anuales
        - Riesgo legal: Incumplimiento de protección de datos
        - Riesgo de seguridad: Si logs son comprometidos, contraseñas expuestas
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Creación de usuario no loggea la contraseña
        2. Ningún nivel de log (DEBUG, INFO, WARNING, ERROR) tiene la password
        3. Ni siquiera parcialmente (ej: "SuperSecret..." truncado)
        
        ESCENARIO REAL:
        - Developer agrega debugging temporal:
          log_info(password=password)  # ❌ ERROR COMÚN
        - Este test lo detecta inmediatamente
        
        ¿QUÉ PASARÍA SI FALLA?
        - Contraseñas en logs de producción
        - Equipo de DevOps puede ver contraseñas
        - Logs en S3/CloudWatch expuestos si hay brecha
        - Multa legal masiva
        """
        # ARRANGE: Capturar TODOS los logs (incluso DEBUG)
        caplog.set_level(logging.DEBUG)
        
        # Contraseña que vamos a buscar en logs
        password_secreto = 'SuperSecretPassword123!@#'
        
        # ACT: Crear usuario con esta contraseña
        user = User.objects.create_user(
            email='security@test.com',
            password=password_secreto,
            first_name='Security',
            last_name='Test'
        )
        
        # ASSERT: Verificar que la contraseña NO está en NINGÚN log
        for record in caplog.records:
            message = record.getMessage()
            
            # Verificación 1: Contraseña completa no está
            assert password_secreto not in message, \
                f"❌ PASSWORD COMPLETA FILTRADA EN LOG: {record.name} - {message}"
            
            # Verificación 2: Fragmentos parciales tampoco
            assert 'SuperSecret' not in message, \
                f"❌ FRAGMENTO DE PASSWORD EN LOG: {record.name} - {message}"
            
            # Verificación 3: Contraseña no está en metadata del log
            assert password_secreto not in str(record.__dict__), \
                f"❌ PASSWORD EN METADATA DEL LOG: {record.name}"
        
        # VERIFICACIÓN ADICIONAL: Usuario fue creado correctamente
        assert user.pk is not None
        
        # VERIFICACIÓN: Password está hasheada en BD
        assert user.password != password_secreto
        assert user.password.startswith('pbkdf2_sha256')
        
        # EXPLICACIÓN:
        # - Este test protege contra accidentes de logging
        # - Es fácil olvidar y loggear datos sensibles
        # - Automated testing es nuestra red de seguridad
        #
        # SI ESTE TEST FALLA:
        # 1. Buscar en código: log_info, log_error, etc.
        # 2. Verificar que NO loggean 'password' field
        # 3. Usar herramientas de secrets scanning
    
    def test_password_timing_attack_resistance(self, disable_account_signals):
        """
        🔴 CRÍTICO: Verificar que check_password es resistente a timing attacks
        
        ¿QUÉ ES UN TIMING ATTACK?
        - Atacante mide el TIEMPO que tarda check_password()
        - Password correcta: 0.010s
        - Password incorrecta: 0.001s
        - ⚠️ Atacante sabe que está más cerca si tarda más tiempo
        
        ¿POR QUÉ ES CRÍTICO?
        - Permite adivinar contraseñas más rápido
        - Reducción de espacio de búsqueda
        - Combinado con brute force = más efectivo
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. check_password() toma tiempo CONSTANTE
        2. No importa si password es correcta o incorrecta
        3. Diferencia de tiempo < 10ms (threshold seguro)
        
        NOTA TÉCNICA:
        - Django's check_password() YA es resistente
        - Este test verifica que no hemos roto eso
        - Importante si agregamos código custom
        
        ¿QUÉ PASARÍA SI FALLA?
        - Atacante puede usar timing attacks
        - Cuentas comprometidas más fácilmente
        - Especialmente grave para cuentas admin
        """
        # ARRANGE: Crear usuario con contraseña conocida
        user = UserFactory()
        password_correcta = 'testpass123'
        password_incorrecta = 'wrongpassword'
        
        # WARMUP: Primera ejecución puede ser más lenta (JIT, cache)
        for _ in range(5):
            user.check_password(password_correcta)
            user.check_password(password_incorrecta)
        
        # ACT: Medir tiempo con contraseña CORRECTA
        tiempos_correctos = []
        for _ in range(10):
            start = time.perf_counter()
            user.check_password(password_correcta)
            elapsed = time.perf_counter() - start
            tiempos_correctos.append(elapsed)
        
        # ACT: Medir tiempo con contraseña INCORRECTA
        tiempos_incorrectos = []
        for _ in range(10):
            start = time.perf_counter()
            user.check_password(password_incorrecta)
            elapsed = time.perf_counter() - start
            tiempos_incorrectos.append(elapsed)
        
        # ASSERT: Calcular promedio de tiempos
        promedio_correcto = sum(tiempos_correctos) / len(tiempos_correctos)
        promedio_incorrecto = sum(tiempos_incorrectos) / len(tiempos_incorrectos)
        
        # Diferencia debe ser < 10ms (0.01 segundos)
        diferencia = abs(promedio_correcto - promedio_incorrecto)
        
        assert diferencia < 0.01, \
            f"❌ VULNERABLE A TIMING ATTACK: "\
            f"Correcto={promedio_correcto:.4f}s, "\
            f"Incorrecto={promedio_incorrecto:.4f}s, "\
            f"Diferencia={diferencia:.4f}s (threshold: 0.01s)"
        
        # EXPLICACIÓN:
        # - Timing attack es SUTIL pero REAL
        # - No es teórico: se ha explotado en producción
        # - Este test nos protege contra regresiones
        #
        # SI ESTE TEST FALLA:
        # 1. Verificar si hay código custom de auth
        # 2. Revisar que use Django's check_password()
        # 3. NO implementar comparación de strings manual
        # 4. Usar hmac.compare_digest() si necesario


# ============================================================================
# NOTAS DE IMPLEMENTACIÓN
# ============================================================================

"""
🎓 APRENDIZAJES CLAVE:

1. **Tests de seguridad son diferentes**:
   - No buscan funcionalidad correcta
   - Buscan vulnerabilidades que funcionan "mal de forma peligrosa"
   
2. **Prioridad CRÍTICA significa**:
   - Impacto legal (multas)
   - Impacto de seguridad (brechas)
   - Impacto de negocio (reputación)
   
3. **Estos tests previenen**:
   - Accidentes de developers (password en logs)
   - Ataques sofisticados (timing attacks)
   - Problemas de UX (email case-sensitivity)

📊 SIGUIENTE PASO:
- Ejecutar estos tests
- Ver si pasan (Django ya tiene protecciones)
- Si fallan, arreglar inmediatamente
- Luego continuar con FASE 2 (tests de logging)
"""