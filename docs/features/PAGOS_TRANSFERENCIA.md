# 💰 GUÍA DE GESTIÓN DE PAGOS POR TRANSFERENCIA

**Fecha de creación:** 10 de Noviembre, 2025  
**Objetivo:** Explicar cómo gestionar pagos manuales por transferencia para clientes fundadores y regulares

---

## 📋 ÍNDICE

1. [Precios Actuales](#precios-actuales)
2. [Identificar Organizaciones Fundadoras](#identificar-organizaciones-fundadoras)
3. [Calcular Precio a Cobrar](#calcular-precio-a-cobrar)
4. [Proceso de Cobro Manual](#proceso-de-cobro-manual)
5. [Ejemplo Práctico](#ejemplo-práctico)

---

## 💵 PRECIOS ACTUALES

### Precio Regular
- **$299 MXN/mes** - Organizaciones regulares

### Precio Fundador
- **$199 MXN/mes** - Organizaciones con membresía fundadora
- **Descuento:** 33.44% sobre el precio regular

---

## 🔍 IDENTIFICAR ORGANIZACIONES FUNDADORAS

### Método 1: Desde el Panel Admin

1. Navegar a `/admin/orgs/organization/`
2. Buscar organizaciones con el badge naranja **"FUNDADOR $199"**
3. Las organizaciones fundadoras tienen una insignia visible

### Método 2: Usando Django Shell

```python
# Listar todas las organizaciones fundadoras
from apps.orgs.models import Organization

fundadoras = Organization.objects.filter(is_founder_member=True)
for org in fundadoras:
    print(f"- {org.name} (ID: {org.id})")
```

### Método 3: Exportar Lista

1. Ir a `/admin/orgs/organization/`
2. Filtrar por "Miembro fundador: Sí" (filtro lateral)
3. Hacer clic en "Exportar" → CSV/Excel
4. Tendrás una lista completa con:
   - Nombre de organización
   - ID
   - Estado de membresía fundadora
   - Fecha de ingreso como fundador

---

## 💰 CALCULAR PRECIO A COBRAR

### Usando el Método del Modelo

El modelo `Organization` tiene un método que calcula automáticamente el precio:

```python
# En Django shell
from apps.orgs.models import Organization

# Obtener organización
org = Organization.objects.get(id=1)  # Cambiar por ID real

# Calcular precio
precio = org.get_founder_price()

print(f"Organización: {org.name}")
print(f"Es fundador: {org.is_founder_member}")
print(f"Precio a cobrar: ${precio} MXN/mes")
```

**Resultado esperado:**
- Si `is_founder_member = True` → Retorna **$199**
- Si `is_founder_member = False` → Retorna **$299**

---

## 📝 PROCESO DE COBRO MANUAL

### 1. Identificar Organizaciones a Cobrar

Al finalizar el mes, genera una lista de organizaciones activas:

```python
from apps.orgs.models import Organization
from datetime import datetime

# Organizaciones activas que deben pagar este mes
orgs_a_cobrar = Organization.objects.filter(
    is_active=True
).select_related('subscription')

print("=" * 60)
print("LISTA DE COBRO - " + datetime.now().strftime("%B %Y"))
print("=" * 60)

for org in orgs_a_cobrar:
    precio = org.get_founder_price()
    tipo = "FUNDADOR" if org.is_founder_member else "REGULAR"
    
    print(f"\n{org.name} (ID: {org.id})")
    print(f"  Tipo: {tipo}")
    print(f"  Precio: ${precio} MXN/mes")
    print(f"  Email contacto: {org.users.first().email if org.users.exists() else 'N/A'}")
```

### 2. Generar Factura/Recibo

**Información a incluir en la factura:**

```
FACTURA #XXXX
Fecha: [Fecha actual]

Cliente: [Nombre de la Organización]
ID: [ID de la organización]

Concepto: Suscripción mensual - Arc Manager
Periodo: [Mes actual]
Tipo de membresía: [FUNDADOR / REGULAR]

Subtotal: $[precio] MXN
IVA (16%): $[precio * 0.16] MXN
Total: $[precio * 1.16] MXN

Datos para transferencia:
  Banco: [Tu banco]
  CLABE: [Tu CLABE]
  Titular: [Nombre de tu empresa]
  Concepto: FACT-XXXX
```

**Cálculo del total con IVA:**

```python
# Ejemplo para fundador
precio_sin_iva = 199
iva = precio_sin_iva * 0.16  # $31.84
total = precio_sin_iva + iva  # $230.84

# Ejemplo para regular
precio_sin_iva = 299
iva = precio_sin_iva * 0.16  # $47.84
total = precio_sin_iva + iva  # $346.84
```

### 3. Enviar Factura al Cliente

**Email de ejemplo:**

```
Asunto: Factura Arc Manager - [Mes] 2025 - [Nombre Organización]

Estimado cliente,

Adjunto encontrará la factura correspondiente al mes de [mes] 
de su suscripción en Arc Manager.

Detalles:
- Organización: [Nombre]
- Plan: [Fundador / Regular]
- Monto: $[total con IVA] MXN
- Fecha límite de pago: [Fecha]

Por favor, realizar la transferencia a:
[Datos bancarios]

Una vez realizado el pago, favor de enviarnos el comprobante 
de transferencia para activar su suscripción.

Gracias por confiar en Arc Manager.

Saludos,
Equipo Arc Manager
```

### 4. Registrar Pago Recibido

Una vez que el cliente envía el comprobante de transferencia:

```python
from apps.plans.models import Subscription
from datetime import datetime, timedelta
from django.utils import timezone

# Obtener suscripción de la organización
org = Organization.objects.get(id=1)  # Cambiar por ID real
subscription = org.subscription

# Extender la suscripción por 1 mes
if subscription:
    # Si está activa, extender desde la fecha actual de vencimiento
    if subscription.is_active:
        nueva_fecha = subscription.end_date + timedelta(days=30)
    else:
        # Si está vencida, extender desde hoy
        nueva_fecha = timezone.now() + timedelta(days=30)
    
    subscription.end_date = nueva_fecha
    subscription.save()
    
    print(f"✅ Pago registrado para {org.name}")
    print(f"   Nueva fecha de vencimiento: {nueva_fecha}")
```

### 5. Confirmar al Cliente

```
Asunto: Pago Recibido - Suscripción Renovada

Estimado cliente,

Confirmamos que hemos recibido su pago de $[monto] MXN.

Su suscripción ha sido renovada exitosamente:
- Organización: [Nombre]
- Válida hasta: [Nueva fecha]

Puede continuar usando Arc Manager sin interrupciones.

Gracias por su pago.

Saludos,
Equipo Arc Manager
```

---

## 🎯 EJEMPLO PRÁCTICO

### Escenario: Cobrar a 3 Organizaciones

**Organizaciones:**
1. **Tech Solutions Inc** (ID: 1) - FUNDADOR
2. **Acme Corp** (ID: 2) - REGULAR
3. **StartupXYZ** (ID: 3) - FUNDADOR

### Paso 1: Generar Lista

```python
from apps.orgs.models import Organization

orgs = [1, 2, 3]  # IDs a cobrar

for org_id in orgs:
    org = Organization.objects.get(id=org_id)
    precio = org.get_founder_price()
    iva = precio * 0.16
    total = precio + iva
    
    print(f"\n{'='*50}")
    print(f"Organización: {org.name}")
    print(f"Tipo: {'FUNDADOR' if org.is_founder_member else 'REGULAR'}")
    print(f"Precio base: ${precio} MXN")
    print(f"IVA (16%): ${iva:.2f} MXN")
    print(f"TOTAL A COBRAR: ${total:.2f} MXN")
```

**Output esperado:**
```
==================================================
Organización: Tech Solutions Inc
Tipo: FUNDADOR
Precio base: $199 MXN
IVA (16%): $31.84 MXN
TOTAL A COBRAR: $230.84 MXN

==================================================
Organización: Acme Corp
Tipo: REGULAR
Precio base: $299 MXN
IVA (16%): $47.84 MXN
TOTAL A COBRAR: $346.84 MXN

==================================================
Organización: StartupXYZ
Tipo: FUNDADOR
Precio base: $199 MXN
IVA (16%): $31.84 MXN
TOTAL A COBRAR: $230.84 MXN
```

### Paso 2: Registrar Pagos (cuando lleguen las transferencias)

```python
from apps.plans.models import Subscription
from datetime import timedelta
from django.utils import timezone

# IDs que ya pagaron
pagos_recibidos = [1, 3]  # Tech Solutions y StartupXYZ pagaron

for org_id in pagos_recibidos:
    org = Organization.objects.get(id=org_id)
    subscription = org.subscription
    
    if subscription:
        # Extender 30 días desde la fecha de vencimiento actual
        subscription.end_date = subscription.end_date + timedelta(days=30)
        subscription.save()
        
        print(f"✅ {org.name} - Renovado hasta {subscription.end_date}")
```

---

## 📊 RESUMEN DE PRECIOS

| Tipo de Membresía | Precio Base | IVA (16%) | Total |
|-------------------|-------------|-----------|-------|
| **FUNDADOR** | $199 MXN | $31.84 MXN | **$230.84 MXN** |
| **REGULAR** | $299 MXN | $47.84 MXN | **$346.84 MXN** |
| **Descuento Fundador** | - | - | **33.44%** |

---

## ⚠️ NOTAS IMPORTANTES

1. **IVA:** Los precios mostrados NO incluyen IVA. Debes agregarlo en la factura (16%)
2. **Fecha de corte:** Puedes cobrar al inicio o al final del mes según tu política
3. **Gracia period:** Considera dar 3-5 días de gracia antes de suspender servicios
4. **Automatización futura:** Este proceso manual es para el MVP. Más adelante se integrará con:
   - Stripe
   - PayPal
   - OXXO Pay
   - Mercado Pago

---

## 🔧 HERRAMIENTAS ÚTILES

### Script de Generación de Reporte Mensual

Crea este archivo: `arc_manager/scripts/generar_reporte_cobros.py`

```python
#!/usr/bin/env python
"""
Script para generar reporte mensual de cobros
Uso: python arc_manager/scripts/generar_reporte_cobros.py
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.orgs.models import Organization

def generar_reporte():
    mes_actual = datetime.now().strftime("%B %Y")
    
    print("=" * 70)
    print(f"REPORTE DE COBROS - {mes_actual}".center(70))
    print("=" * 70)
    
    orgs_activas = Organization.objects.filter(is_active=True)
    
    total_fundadores = 0
    total_regulares = 0
    monto_fundadores = 0
    monto_regulares = 0
    
    print("\n📋 ORGANIZACIONES FUNDADORAS:")
    print("-" * 70)
    
    for org in orgs_activas.filter(is_founder_member=True):
        precio = org.get_founder_price()
        total_con_iva = precio * 1.16
        print(f"  {org.name:40} ${total_con_iva:>8.2f} MXN")
        total_fundadores += 1
        monto_fundadores += total_con_iva
    
    print("\n📋 ORGANIZACIONES REGULARES:")
    print("-" * 70)
    
    for org in orgs_activas.filter(is_founder_member=False):
        precio = org.get_founder_price()
        total_con_iva = precio * 1.16
        print(f"  {org.name:40} ${total_con_iva:>8.2f} MXN")
        total_regulares += 1
        monto_regulares += total_con_iva
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN:")
    print("-" * 70)
    print(f"  Fundadores: {total_fundadores:>4} orgs  →  ${monto_fundadores:>10.2f} MXN")
    print(f"  Regulares:  {total_regulares:>4} orgs  →  ${monto_regulares:>10.2f} MXN")
    print("-" * 70)
    print(f"  TOTAL:      {total_fundadores + total_regulares:>4} orgs  →  ${monto_fundadores + monto_regulares:>10.2f} MXN")
    print("=" * 70)

if __name__ == '__main__':
    generar_reporte()
```

**Ejecutar:**
```bash
python arc_manager/scripts/generar_reporte_cobros.py
```

---

## ✅ CHECKLIST DE PROCESO MENSUAL

- [ ] Día 1 del mes: Generar reporte de organizaciones activas
- [ ] Día 1-3: Generar y enviar facturas a todos los clientes
- [ ] Día 3-10: Recibir transferencias y comprobantes
- [ ] Día 10-15: Registrar pagos en el sistema
- [ ] Día 15-20: Seguimiento a clientes que no han pagado
- [ ] Día 25: Suspender organizaciones sin pago (desactivar)
- [ ] Día 28: Reporte final del mes

---

**Autor:** GitHub Copilot  
**Fecha:** 10 de Noviembre, 2025  
**Versión:** 1.0
