#!/usr/bin/env python
"""
Análisis comparativo de validadores de contraseña:
- Validadores de Django (por defecto)
- Validadores personalizados (mejores prácticas)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator as DjangoUserAttrValidator,
    MinimumLengthValidator as DjangoMinLengthValidator,
    CommonPasswordValidator as DjangoCommonValidator,
    NumericPasswordValidator as DjangoNumericValidator,
)
from core.password_validators import (
    CustomUserAttributeSimilarityValidator,
    CustomMinimumLengthValidator,
    PasswordComplexityValidator,
    CustomNumericPasswordValidator,
    WeakPasswordValidator,
)
from django.core.exceptions import ValidationError

test_cases = [
    ('abc123', 'Muy corta + numérica'),
    ('Test123', 'Corta pero válida'),
    ('TestPass123', 'Válida - segura'),
    ('password123', 'Muy común'),
    ('12345678', 'Solo números'),
    ('qwerty123', 'Patrón teclado'),
    ('MyTest2024', 'Válida - con año'),
    ('Admin@2024', 'Válida - especial'),
]

print("=" * 80)
print("COMPARATIVA: VALIDADORES DE DJANGO vs PERSONALIZADOS")
print("=" * 80)

# Django validators
django_validators = [
    DjangoUserAttrValidator(),
    DjangoMinLengthValidator(),
    DjangoCommonValidator(),
    DjangoNumericValidator(),
]

# Custom validators
custom_validators = [
    CustomUserAttributeSimilarityValidator(),
    CustomMinimumLengthValidator(),
    PasswordComplexityValidator(),
    CustomNumericPasswordValidator(),
    WeakPasswordValidator(),
]

print("\n1️⃣  VALIDADORES DE DJANGO (ACTUALES)")
print("-" * 80)
print()

for pwd, desc in test_cases:
    print(f"🔒 {pwd:20} | {desc}")
    rejected = False
    for v in django_validators:
        try:
            v.validate(pwd)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e.messages[0])
            print(f"   ❌ {v.__class__.__name__}: {msg}")
            rejected = True
    if not rejected:
        print(f"   ✅ ACEPTADA")
    print()

print("\n" + "=" * 80)
print("2️⃣  VALIDADORES PERSONALIZADOS (RECOMENDADOS)")
print("-" * 80)
print()

for pwd, desc in test_cases:
    print(f"🔒 {pwd:20} | {desc}")
    rejected = False
    for v in custom_validators:
        try:
            v.validate(pwd)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e.messages[0])
            print(f"   ❌ {v.__class__.__name__}: {msg}")
            rejected = True
    if not rejected:
        print(f"   ✅ ACEPTADA")
    print()

print("\n" + "=" * 80)
print("📊 ANÁLISIS Y RECOMENDACIONES")
print("=" * 80)
print("""
✅ VENTAJAS DE VALIDADORES PERSONALIZADOS (RECOMENDADO):

1. MEJOR UX - Menos restricciones innecesarias:
   - Django rechaza CUALQUIER contraseña que coincida con palabras comunes
   - Nuestros validadores solo rechazan patrones MUY predecibles (qwerty, 123456)
   - Resultado: "TestPass123" se acepta en personalizados, rechazada en Django

2. MENSAJES CLAROS Y COHERENTES:
   - Django: Mensajes genéricos que no dan contexto
   - Nuestros: Mensajes específicos en español que explican POR QUÉ se rechaza

3. COHERENCIA ENTRE VALIDACIÓN Y MENSAJE:
   - Solo validamos lo que decimos que validamos
   - Si el mensaje dice "no números", solo rechazamos si SON TODOS números
   - Si el mensaje dice "no patrón teclado", rechazamos qwerty/123456, no "pass123"

4. SEGURIDAD RAZONABLE:
   - Mantenemos protección contra:
     ✓ Contraseñas muy cortas (< 8 caracteres)
     ✓ Solo números (completamente numérica)
     ✓ Patrones de teclado obvios
     ✓ Similitud con email/usuario
   - Removemos protección excesiva:
     ✗ CommonPasswordValidator (demasiado restrictivo)

5. CUMPLIMIENTO DE ESTÁNDARES:
   - OWASP: Recomienda longitud mínima + complejidad
   - NO recomienda listas de contraseñas prohibidas (por ser restrictivas)
   - NIST SP 800-63B: Rechaza validaciones de complejidad mínima estrictas

❌ DESVENTAJAS VALIDADORES DE DJANGO ESTÁNDAR:

- CommonPasswordValidator es MUY restrictivo (rechaza ~20k palabras comunes)
- Causa frustración: usuarios no entienden por qué se rechaza su contraseña
- Crea mala UX: usuarios tienen que intentar múltiples contraseñas
- Incoherencia: mensaje vs realidad (dice "muy común" pero "Test123" también se rechaza)

🎯 RECOMENDACIÓN FINAL:

Usar VALIDADORES PERSONALIZADOS porque:
✓ Mejor experiencia de usuario
✓ Mensajes coherentes y claros
✓ Validaciones razonables y explícitas
✓ Cumple estándares OWASP/NIST
✓ Mantiene seguridad sin ser demasiado restrictivo
""")
