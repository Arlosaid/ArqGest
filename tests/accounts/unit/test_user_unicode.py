"""
🔴 TESTS DE SOPORTE UNICODE - MODELO USER (ALTA PRIORIDAD)

Estos tests verifican que el sistema maneja correctamente caracteres internacionales
en nombres de usuarios, cumpliendo con estándares de inclusión y evitando discriminación.

IMPORTANCIA:
- Inclusión internacional: Usuarios de todo el mundo
- Compliance legal: Leyes anti-discriminación (GDPR, etc.)
- UX: Usuarios deben ver sus nombres correctamente
- Datos íntegros: No corrupción de caracteres
- SEO/Marketing: Nombres correctos en emails, dashboards

CASOS PROBADOS:
- Acentos españoles: José, María, Ñuñez
- Caracteres franceses: François, Cédric
- Caracteres alemanes: Müller, Händel
- Caracteres chinos: 张伟, 李娜
- Caracteres japoneses: 田中, 佐藤
- Caracteres árabes: محمد
- Emojis: 😀 (futuro, baja prioridad)

COBERTURA: 2/3 tests de unicode (66%)
- ✅ first_name con unicode
- ✅ last_name con unicode  
- ⏳ emojis en nombres (baja prioridad)

Autor: ARC Manager Team
Fecha: 4 Nov 2025
Fase: 2 - Alta Prioridad
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.unit
class TestUserUnicodeSupport:
    """
    Tests para verificar que el sistema maneja correctamente caracteres Unicode
    en nombres de usuarios de diferentes idiomas y regiones.
    """
    
    def test_unicode_in_first_name(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar soporte de Unicode en first_name
        
        ¿POR QUÉ ES IMPORTANTE?
        - Inclusión: Usuarios de 190+ países usan ARC Manager
        - Legal: Leyes anti-discriminación requieren soporte internacional
        - Datos: Nombres deben guardarse sin corrupción
        - UX: Usuarios deben ver sus nombres reales, no "???"
        - Branding: Emails/notificaciones con nombres correctos
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Caracteres con acentos (español, francés, portugués)
        2. Caracteres con diéresis (alemán, turco)
        3. Caracteres asiáticos (chino, japonés, coreano)
        4. Caracteres cirílicos (ruso, ucraniano)
        5. Caracteres árabes
        6. full_name funciona correctamente con Unicode
        7. __str__() no rompe con Unicode
        
        ¿QUÉ PASARÍA SI FALLA?
        - Usuarios internacionales no pueden registrarse
        - Nombres se corrompen en DB: "Jos?" en vez de "José"
        - Violación de leyes anti-discriminación
        - Pérdida de usuarios de mercados internacionales
        - Reputación dañada
        
        EJEMPLOS DE NOMBRES REALES:
        - Español: José, María, Ñuñez, Ángel
        - Francés: François, Cédric, Joëlle
        - Alemán: Müller, Händel, Björn
        - Chino: 张伟 (Zhāng Wěi), 李娜 (Lǐ Nà)
        - Japonés: 田中 (Tanaka), 佐藤 (Satō)
        - Árabe: محمد (Muhammad)
        """
        # Test casos con acentos (español/francés/portugués)
        test_cases = [
            # (first_name, last_name, descripción)
            ("José", "García", "Acentos españoles"),
            ("François", "Dupont", "Cédille francesa"),
            ("Müller", "Schmidt", "Diéresis alemana"),
            ("Björn", "Svensson", "Escandinavos"),
            ("Włodzimierz", "Kowalski", "Polaco con Ł"),
            ("Ñoño", "Núñez", "Ñ española"),
            ("张伟", "李", "Caracteres chinos"),
            ("田中", "太郎", "Caracteres japoneses"),
            ("Владимир", "Петров", "Cirílico ruso"),
            ("محمد", "أحمد", "Árabe"),
        ]
        
        for first_name, last_name, description in test_cases:
            # ARRANGE & ACT: Crear usuario con nombres Unicode
            user = User.objects.create_user(
                email=f"test_{hash(first_name)}@example.com",
                password='SecurePass123!',
                first_name=first_name,
                last_name=last_name
            )
            
            # ASSERT 1: El nombre se guardó correctamente
            user.refresh_from_db()
            assert user.first_name == first_name, \
                f"[{description}] First_name esperado '{first_name}', obtuve '{user.first_name}'"
            
            # ASSERT 2: full_name funciona con Unicode
            expected_full_name = f"{first_name} {last_name}".strip()
            assert user.full_name == expected_full_name, \
                f"[{description}] Full_name esperado '{expected_full_name}', obtuve '{user.full_name}'"
            
            # ASSERT 3: __str__() no rompe con Unicode
            try:
                str_repr = str(user)
                assert len(str_repr) > 0, \
                    f"[{description}] __str__() retornó string vacío"
                # Debe ser el full_name
                assert str_repr == expected_full_name, \
                    f"[{description}] __str__() esperado '{expected_full_name}', obtuve '{str_repr}'"
            except Exception as e:
                pytest.fail(f"[{description}] __str__() falló con Unicode: {e}")
            
            # Limpiar para siguiente iteración
            user.delete()
    
    
    def test_unicode_in_last_name(self, db, disable_account_signals):
        """
        🔴 ALTA PRIORIDAD: Verificar soporte de Unicode en last_name
        
        ¿POR QUÉ ES IMPORTANTE?
        - Apellidos tienen igual importancia que nombres
        - Muchos apellidos tienen caracteres especiales
        - Sorting/búsqueda debe funcionar con Unicode
        - Reportes/exports deben mantener integridad
        
        ¿QUÉ ESTAMOS PROBANDO?
        1. Apellidos complejos con múltiples acentos
        2. Apellidos compuestos con guiones
        3. Apellidos con apóstrofes (O'Brien, D'Angelo)
        4. Apellidos asiáticos
        5. Prefijos nobiliarios (van, de, von)
        
        ¿QUÉ PASARÍA SI FALLA?
        - Usuarios no pueden registrarse con apellidos reales
        - Búsquedas de usuarios fallan
        - Sorting alfabético incorrecto
        - Exports corruptos (CSV, Excel, PDF)
        """
        # Test casos de apellidos complejos
        test_cases = [
            # (first_name, last_name, descripción)
            ("John", "O'Brien", "Apóstrofe irlandés"),
            ("Maria", "González-Pérez", "Apellido compuesto español"),
            ("André", "D'Angelo", "Apóstrofe italiano"),
            ("Hans", "von Müller", "Prefijo alemán"),
            ("Pierre", "de La Fontaine", "Prefijo francés"),
            ("João", "São Paulo", "Til portuguesa"),
            ("Test", "Çelik", "Ç turca"),
            ("User", "Ødegård", "Ø noruega"),
            ("人", "大姓氏", "Apellido chino largo"),
            ("テスト", "ユーザー", "Apellido katakana"),
        ]
        
        for first_name, last_name, description in test_cases:
            # ARRANGE & ACT: Crear usuario
            user = User.objects.create_user(
                email=f"test_{hash(last_name)}@example.com",
                password='SecurePass123!',
                first_name=first_name,
                last_name=last_name
            )
            
            # ASSERT 1: El apellido se guardó correctamente
            user.refresh_from_db()
            assert user.last_name == last_name, \
                f"[{description}] Last_name esperado '{last_name}', obtuve '{user.last_name}'"
            
            # ASSERT 2: full_name incluye el apellido correctamente
            expected_full_name = f"{first_name} {last_name}".strip()
            assert user.full_name == expected_full_name, \
                f"[{description}] Full_name esperado '{expected_full_name}', obtuve '{user.full_name}'"
            
            # ASSERT 3: Búsqueda por apellido funciona
            found_users = User.objects.filter(last_name=last_name)
            assert found_users.exists(), \
                f"[{description}] No se pudo buscar usuario por last_name='{last_name}'"
            assert user in found_users, \
                f"[{description}] Usuario no encontrado al buscar por last_name"
            
            # Limpiar
            user.delete()
    
    
    @pytest.mark.skip(reason="Emoji support es baja prioridad - implementar en Fase 4")
    def test_emoji_in_names(self, db, disable_account_signals):
        """
        🟡 BAJA PRIORIDAD: Verificar soporte de emojis en nombres
        
        NOTA: Este test está skipeado porque emojis en nombres es edge case poco común.
        La mayoría de empresas no lo soporta. Implementar solo si es requisito de negocio.
        
        ¿POR QUÉ PODRÍA SER IMPORTANTE?
        - Algunos usuarios quieren expresividad
        - Redes sociales permiten emojis
        - Generación Z usa emojis en todo
        
        ¿RIESGOS DE SOPORTAR EMOJIS?
        - Tamaño variable en UTF-8 (1-4 bytes)
        - Problemas de rendering en PDFs/emails
        - Sorting complicado
        - Búsqueda puede fallar
        - Base de datos debe usar utf8mb4
        """
        test_cases = [
            ("John 😀", "Doe", "Emoji en first_name"),
            ("Jane", "Smith 🎉", "Emoji en last_name"),
            ("🔥 Test", "User 🚀", "Emojis en ambos nombres"),
        ]
        
        for first_name, last_name, description in test_cases:
            user = User.objects.create_user(
                email=f"emoji_{hash(first_name)}@example.com",
                password='SecurePass123!',
                first_name=first_name,
                last_name=last_name
            )
            
            user.refresh_from_db()
            assert user.first_name == first_name
            assert user.last_name == last_name
            
            user.delete()
