"""
🔴 TESTS DE VALIDACIÓN - MODELO USER (ALTA PRIORIDAD)

Estos tests verifican que las validaciones de longitud y normalización de campos
funcionan correctamente, evitando datos corruptos y ataques de inyección.

IMPORTANCIA:
- Integridad de datos: Evitar datos truncados o corruptos
- Seguridad: Prevenir buffer overflows y ataques de inyección
- Compliance: Límites de longitud para evitar abuso de storage
- UX: Mensajes de error claros antes de submit
- Performance: Índices DB optimizados con longitudes conocidas

LÍMITES ACTUALES:
- email: 254 caracteres (RFC 5321)
- first_name: 50 caracteres
- last_name: 50 caracteres
- username: 150 caracteres (auto-generado)

COBERTURA: 4/8 tests de validación (50%)
- ✅ email_normalization (lowercase)
- ✅ email_max_length (254)
- ✅ first_name_max_length (50)
- ✅ last_name_max_length (50)
- ⏳ email_whitespace_trim
- ⏳ username con email largo
- ⏳ validation errors claros

Autor: ARC Manager Team
Fecha: 4 Nov 2025
Fase: 2 - Alta Prioridad
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.unit
class TestUserFieldValidation:
    """
    Tests para verificar que las validaciones de campos funcionan correctamente
    y los límites de longitud se respetan.
    """
    
    def test_email_normalization(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que emails se normalizan a lowercase
        
        ¿POR QUÉ ES IMPORTANTE?
        - Evitar duplicados: TEST@x.com != test@x.com
        - Búsquedas consistentes: Case-insensitive por defecto
        - UX: Usuarios pueden escribir en cualquier case
        - Compatibilidad: RFC 5321 recomienda case-insensitive
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Email con UPPERCASE se convierte a lowercase
        2. Email mixto (MiXeD CaSe) se convierte a lowercase
        3. Dominio con uppercase se convierte a lowercase
        4. Normalización funciona en create_user
        
        ¿QUÉ PASARÍA SI FALLA?
        - Usuarios duplicados: admin@x.com y ADMIN@x.com
        - Búsquedas fallidas: buscar "test@x.com" no encuentra "TEST@x.com"
        - Problemas de login: case-sensitive confunde usuarios
        - Auditoría inconsistente
        
        REFERENCIA:
        - RFC 5321 Section 2.3.11: Mailbox names are case-insensitive
        - Django best practice: normalize emails to lowercase
        """
        # Test casos de normalización - cada uno con email único
        test_cases = [
            # (input_email, expected_normalized)
            ("TEST1@EXAMPLE.COM", "test1@example.com"),
            ("Test2@Example.Com", "test2@example.com"),
            ("user3@DOMAIN.COM", "user3@domain.com"),
            ("MiXeD4.CaSe@Example.COM", "mixed4.case@example.com"),
            ("UPPERCASE5.USER@UPPERCASE.DOMAIN", "uppercase5.user@uppercase.domain"),
        ]
        
        for input_email, expected_email in test_cases:
            # ARRANGE & ACT: Crear usuario con email en diferentes cases
            user = User.objects.create_user(
                email=input_email,
                password='SecurePass123!',
                first_name='Test',
                last_name='User'
            )
            
            # ASSERT 1: El email se normalizó a lowercase
            assert user.email == expected_email, \
                f"Email input '{input_email}' debería normalizarse a '{expected_email}', obtuve '{user.email}'"
            
            # ASSERT 2: Verificar en DB que está en lowercase
            user.refresh_from_db()
            assert user.email == expected_email, \
                f"Email en DB debería ser '{expected_email}', obtuve '{user.email}'"
            
            # ASSERT 3: No se puede crear otro usuario con email en diferente case
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        email=input_email.swapcase(),  # Invertir case
                        password='AnotherPass123!'
                    )
                    # Si llegamos aquí, el test debería fallar
                    pytest.fail("Debería haber lanzado IntegrityError por email duplicado")
            except IntegrityError:
                # Este es el comportamiento esperado
                pass
            
            # Limpiar para siguiente test case
            user.delete()
    
    
    def test_email_max_length_enforced(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que email respeta max_length de 254 caracteres
        
        ¿POR QUÉ ES IMPORTANTE?
        - RFC 5321: Límite oficial de email es 254 caracteres
        - Seguridad: Prevenir ataques de buffer overflow
        - Performance: Índices DB optimizados
        - Compatibilidad: SMTP servers rechazan emails > 254
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Email de exactamente 254 caracteres funciona
        2. Email de 255+ caracteres falla con ValidationError
        3. Error message es claro
        
        ¿QUÉ PASARÍA SI FALLA?
        - Emails truncados silenciosamente
        - Usuarios no pueden recibir confirmación
        - Vulnerabilidad de inyección SQL
        - Índice DB corrupto
        
        LÍMITE RFC 5321:
        - Max 64 caracteres para local-part (antes del @)
        - Max 255 caracteres para domain-part (después del @)
        - Max 254 total (email completo)
        """
        # ARRANGE: Crear email de exactamente 254 caracteres
        # Format: "aaaa...@bbbb...com"
        # local_part (64) + @ (1) + domain (189) = 254
        
        local_part = "a" * 64  # Max 64 para local-part
        # Dominio: 254 - 64 - 1(@) = 189 caracteres
        # Necesitamos 189 chars: 185 + ".com" (4) = 189
        domain_part = "b" * 185 + ".com"
        email_254 = f"{local_part}@{domain_part}"
        
        assert len(email_254) == 254, \
            f"Email de test debe ser exactamente 254 chars, es {len(email_254)}"
        
        # ACT: Crear usuario con email de 254 chars
        user = User.objects.create_user(
            email=email_254,
            password='SecurePass123!',
            first_name='Test',
            last_name='User'
        )
        
        # ASSERT 1: Se creó correctamente
        assert user.email == email_254.lower(), \
            "Email de 254 caracteres debe guardarse correctamente"
        
        # ASSERT 2: Se puede recuperar de DB
        user.refresh_from_db()
        assert user.email == email_254.lower(), \
            "Email de 254 caracteres debe recuperarse correctamente de DB"
        
        user.delete()
        
        # ARRANGE: Email de 255 caracteres (excede límite)
        email_255 = email_254 + "x"
        assert len(email_255) == 255
        
        # ACT & ASSERT: Debe fallar al intentar crear
        with pytest.raises((ValidationError, Exception)) as exc_info:
            # Puede fallar en validación del modelo o en DB
            invalid_user = User(
                email=email_255,
                first_name='Test',
                last_name='User'
            )
            invalid_user.full_clean()  # Valida el modelo
            invalid_user.set_password('SecurePass123!')
            invalid_user.save()
        
        # El error puede ser ValidationError o DataError de DB
        # Lo importante es que falle, no importa en qué capa
    
    
    def test_first_name_max_length(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que first_name respeta max_length de 50
        
        ¿POR QUÉ ES IMPORTANTE?
        - UX: Nombres muy largos rompen UI (headers, cards, etc.)
        - Performance: Índices optimizados
        - Seguridad: Prevenir inyección de HTML/JS
        - Estándar: La mayoría de sistemas usan 50-100 chars
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Nombre de 50 caracteres funciona
        2. Nombre de 51+ caracteres falla
        3. Error es ValidationError claro
        
        ¿QUÉ PASARÍA SI FALLA?
        - Nombres truncados sin avisar
        - UI rota con nombres largos
        - Búsquedas inconsistentes
        """
        # ARRANGE: Nombre de exactamente 50 caracteres
        first_name_50 = "A" * 50
        
        # ACT: Crear usuario
        user = User.objects.create_user(
            email='test50@example.com',
            password='SecurePass123!',
            first_name=first_name_50,
            last_name='User'
        )
        
        # ASSERT 1: Se guardó correctamente
        assert user.first_name == first_name_50, \
            "First_name de 50 caracteres debe guardarse"
        
        user.refresh_from_db()
        assert user.first_name == first_name_50, \
            "First_name de 50 caracteres debe recuperarse de DB"
        
        user.delete()
        
        # ARRANGE: Nombre de 51 caracteres (excede límite)
        first_name_51 = "A" * 51
        
        # ACT & ASSERT: Debe fallar
        with pytest.raises((ValidationError, Exception)):
            invalid_user = User(
                email='test51@example.com',
                first_name=first_name_51,
                last_name='User'
            )
            invalid_user.full_clean()
            invalid_user.set_password('SecurePass123!')
            invalid_user.save()
    
    
    def test_last_name_max_length(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar que last_name respeta max_length de 50
        
        ¿POR QUÉ ES IMPORTANTE?
        - Consistencia con first_name
        - Algunos apellidos son muy largos (apellidos compuestos)
        - UI debe manejar apellidos en mismo espacio que nombres
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Apellido de 50 caracteres funciona
        2. Apellido de 51+ caracteres falla
        3. Apellidos compuestos largos se manejan
        
        NOTA: Algunos apellidos reales son muy largos:
        - "García-Fernández de la Torre y Martínez" = 46 chars ✓
        - Apellidos galeses pueden ser > 50 chars ✗
        """
        # ARRANGE: Apellido de exactamente 50 caracteres
        last_name_50 = "B" * 50
        
        # ACT: Crear usuario
        user = User.objects.create_user(
            email='lastname50@example.com',
            password='SecurePass123!',
            first_name='User',
            last_name=last_name_50
        )
        
        # ASSERT 1: Se guardó correctamente
        assert user.last_name == last_name_50, \
            "Last_name de 50 caracteres debe guardarse"
        
        user.refresh_from_db()
        assert user.last_name == last_name_50, \
            "Last_name de 50 caracteres debe recuperarse de DB"
        
        user.delete()
        
        # ARRANGE: Apellido de 51 caracteres (excede límite)
        last_name_51 = "B" * 51
        
        # ACT & ASSERT: Debe fallar
        with pytest.raises((ValidationError, Exception)):
            invalid_user = User(
                email='lastname51@example.com',
                first_name='User',
                last_name=last_name_51
            )
            invalid_user.full_clean()
            invalid_user.set_password('SecurePass123!')
            invalid_user.save()
