# 📋 Guía de Tests de Validación de Pagos y Presupuesto

## 🎯 Objetivo General

Crear una suite de tests **útil para encontrar bugs reales** en el módulo de finanzas de proyectos, enfocándose especialmente en la validación de presupuesto al crear y editar pagos.

---

## 🐛 El Error Que Se Corrigió (TC-52)

### ❌ El Problema Original

**Escenario:**
1. Presupuesto del proyecto: $10,000
2. Se crea un pago de $5,000 ✅
3. Se intenta **EDITAR** ese pago a $11,000 ❌

**Lo que pasaba (BUG):** La vista permitía editar el pago a $11,000, excediendo el presupuesto.

**Lo que debería pasar:** La vista debe RECHAZAR la edición mostrando un mensaje de error indicando el máximo permitido.

### ✅ La Solución (En PaymentUpdateView.form_valid())

```python
# Calcular el nuevo total considerando el cambio
new_total = (self.project.total_paid - old_amount) + new_amount

if new_total > self.project.total_budget:
    max_allowed = self.project.total_budget - (self.project.total_paid - old_amount)
    # Rechazar la edición con mensaje de error
```

---

## 📁 Archivos de Tests Creados

### 1. `test_payment_budget_validation.py` - Validación de Presupuesto

**Objetivo:** Verificar que creación y edición de pagos respeten el presupuesto.

#### Tests principales:

| Test | Verifica | Bug que busca |
|------|----------|---------------|
| `test_create_payment_within_budget` | Pago dentro del presupuesto ✅ | N/A - prueba positiva |
| `test_create_payment_exactly_budget` | Pago exacto al presupuesto | División por cero en remaining_amount |
| `test_create_multiple_payments_cumulatively_exceeding_budget` | 2+ pagos que juntos exceden | Falta validación en creación |
| `test_edit_payment_increase_within_budget` | Aumentar pago dentro del saldo | Cálculo incorrecto de new_total |
| **`test_edit_payment_exceed_budget_should_fail`** | ⭐ **ESTE ERA EL BUG PRINCIPAL** | No rechazaba edición que excedía presupuesto |
| `test_edit_payment_with_multiple_existing_payments` | Editar con varios pagos | Cálculo incorrecto cuando hay múltiples pagos |
| `test_edit_payment_exceeding_with_multiple_payments` | Editar que haría exceder con otros | Falta validación de suma total |
| `test_create_payment_with_zero_amount` | Pago de $0 | Permite montos <= 0 |
| `test_create_payment_with_negative_amount` | Pago negativo | Permite montos negativos |
| `test_payment_with_unicode_description` | Descripción con caracteres especiales | Encoding de base de datos |
| `test_complete_flow_from_no_budget_to_payments` | Flujo completo TC-52 | Integración de todos los errores |

---

### 2. `test_payment_advanced_scenarios.py` - Escenarios Complejos

**Objetivo:** Encontrar bugs en interacciones complejas y cálculos financieros.

#### Tests principales:

| Test | Verifica | Bug que busca |
|------|----------|---------------|
| `test_remaining_amount_with_no_budget` | Monto restante sin presupuesto | Manejo de None en operaciones |
| `test_remaining_amount_negative_overflow` | Saldo negativo | Sobrepago no detectado |
| `test_many_small_payments_accumulation` | 100 pagos de $100 | Precisión decimal acumulada |
| `test_payments_with_different_dates_sum_correctly` | Pagos en fechas diferentes | La fecha afecta el total |
| `test_edit_multiple_payments_in_sequence` | Editar secuencialmente | Cache desactualizado |
| `test_exact_budget_match_with_many_decimals` | $1,234.56 presupuesto | Redondeo incorrecto |
| `test_three_decimal_places_not_allowed` | Más de 2 decimales | Modelo permite 3 decimales |
| `test_very_large_budget` | Máximo permitido (9,999,999,999.99) | Overflow de DecimalField |
| `test_very_small_budget` | Presupuesto de $0.01 | División por cero |
| `test_two_users_try_edit_payment_concurrently` | Race condition | Pérdida de cambios en edición concurrente |
| `test_payments_ordered_by_date_descending` | Ordenamiento por fecha | Orden incorrecto |

---

### 3. `test_payment_integration_views.py` - Integración con Vistas

**Objetivo:** Simular exactamente lo que hacen PaymentCreateView y PaymentUpdateView.

#### Tests principales:

| Test | Simula | Bug que busca |
|------|--------|---------------|
| **`test_validate_update_exceed_budget_main_bug`** | ⭐ **PaymentUpdateView.form_valid()** | **EL ERROR DE TC-52** |
| `test_validate_create_positive_amount_within_budget` | PaymentCreateView con monto válido | N/A - prueba positiva |
| `test_validate_create_zero_amount` | Crear pago de $0 | No rechaza $0 |
| `test_validate_create_negative_amount` | Crear pago negativo | No rechaza negativos |
| `test_validate_create_exceeding_budget` | Superar presupuesto en creación | No valida presupuesto en creación |
| `test_validate_create_with_existing_payment` | Crear con pagos existentes | Cálculo de total_paid incorrecto |
| `test_validate_create_exactly_remaining` | Pago por cantidad restante exacta | Cálculo de remaining_amount |
| `test_validate_update_decrease` | Disminuir pago | Permite pero calcula mal |
| `test_validate_update_with_multiple_payments` | Editar con varios pagos | Cálculo con múltiples pagos |
| `test_validate_update_with_multiple_payments_exceed` | Editar que haría exceder | No rechaza correctamente |
| `test_complete_flow_as_per_tc52_specification` | **Flujo exacto de TC-52** | Cualquier error del flujo |
| `test_workflow_with_multiple_editions` | Múltiples creaciones y ediciones | Bugs en operaciones secuenciales |

---

## 🔍 Bugs Potenciales Que Buscan Encontrar

### 1. **Validación de Presupuesto**

```
✓ Crear pago dentro del presupuesto → Debe pasar
✗ Crear pago que exceda presupuesto → Debe rechazarse
✗ Editar pago para que exceda presupuesto → Debe rechazarse (ESTE ERA EL BUG)
```

### 2. **Validación de Montos**

```
✗ Crear pago de $0 → Debe rechazarse
✗ Crear pago negativo → Debe rechazarse
✗ Editar pago a $0 → Debe rechazarse
✗ Editar pago a negativo → Debe rechazarse
```

### 3. **Cálculos Financieros**

```
? Precisión decimal: ¿Se redondea correctamente?
? Suma de múltiples pagos: ¿Da el total correcto?
? Remaining amount: ¿Cálculo correcto cuando > presupuesto?
? Porcentaje: ¿Se calcula bien?
```

### 4. **Casos Extremos**

```
? Presupuesto muy grande (máximo: 9,999,999,999.99)
? Presupuesto muy pequeño ($0.01)
? Múltiples pagos (100+)
? Valores con muchos decimales
? Caracteres especiales en descripciones
```

### 5. **Concurrencia**

```
? Dos usuarios editando el mismo pago
? Cache desactualizado en ediciones secuenciales
? Fallo en invalidación de cache
```

### 6. **Integridad de Datos**

```
? Pago se elimina cuando se elimina proyecto (CASCADE)
? created_by es NULL cuando se elimina usuario (SET_NULL)
? Índices funcionan correctamente
```

---

## 🚀 Cómo Ejecutar los Tests

### Ejecutar todos los tests de finanzas:

```bash
pytest tests/projects/unit/test_payment_*.py -v
```

### Ejecutar solo el test del bug principal (TC-52):

```bash
pytest tests/projects/unit/test_payment_integration_views.py::TestPaymentUpdateViewValidation::test_validate_update_exceed_budget_main_bug -v
```

### Ejecutar con coverage:

```bash
pytest tests/projects/unit/test_payment_*.py --cov=apps.projects.models --cov-report=html
```

### Ejecutar en modo verbose:

```bash
pytest tests/projects/unit/test_payment_budget_validation.py -vv -s
```

---

## 📊 Cobertura de Tests

### Modelos Cubiertos:

- ✅ `ProjectPayment` - Creación, edición, eliminación
- ✅ `Project.total_paid` - Property que suma pagos
- ✅ `Project.remaining_amount` - Property que calcula saldo
- ✅ Métodos `save()` y `delete()` de ProjectPayment

### Vistas Simuladas:

- ✅ `PaymentCreateView.form_valid()` - Validación de creación
- ✅ `PaymentUpdateView.form_valid()` - Validación de edición
- ✅ Invalidación de cache después de CRUD
- ✅ Mensajes de error al usuario

### Casos Cubiertos:

- ✅ Flujo normal (create, read, update, delete)
- ✅ Validaciones de presupuesto
- ✅ Validaciones de montos
- ✅ Edge cases (ceros, negativos, valores extremos)
- ✅ Múltiples pagos y usuarios
- ✅ Cálculos financieros
- ✅ Cache invalidation

---

## ⚠️ Advertencias Importantes

### Tests que revelan BUGS ACTUALES:

Algunos tests marcan con comentarios `# ⚠️ POTENCIAL BUG:` - estos tests muestran que:

1. **El modelo NO valida montos positivos** - Permite crear pagos de $0 o negativos
   - Lugar de corrección: `apps.projects.models.ProjectPayment.clean()` o validador

2. **El modelo NO valida fechas futuras** - Permite pagos con fecha en el futuro
   - Lugar de corrección: Validador en el modelo o la vista

3. **Sin presupuesto, se permiten pagos ilimitados** - Esto es correcto según las reglas
   - Pero la UI debería prevenir esto (presupuesto es required)

### Tests que son PRUEBAS POSITIVAS:

Algunos tests (sin ⚠️) verifican que funciona correctamente:

```python
def test_edit_payment_increase_within_budget(self):
    """✅ CORRECTO: Aumentar pago dentro del saldo disponible debe funcionar."""
```

Estos tests se verán VERDES si el código funciona correctamente.

---

## 🔧 Cómo Usar Esta Suite para Desarrollo

### Cuando reportan un bug:

1. **Identifica el caso** - ¿Cuál test lo reproduce?
2. **Ejecuta el test** - Verifica que falla (RED)
3. **Corrige el código** - Implementa la solución
4. **Ejecuta el test** - Verifica que pasa (GREEN)
5. **Ejecuta todos los tests** - Asegura no haber roto nada (REGRESSION)

### Cuando agregas una feature:

1. **Crea un test** que verifique la feature
2. **Verifica que falla** (RED)
3. **Implementa la feature** 
4. **Verifica que el test pasa** (GREEN)
5. **Verifica que otros tests siguen pasando** (REGRESSION)

---

## 📈 Métricas de Calidad

### Cobertura esperada:

```
Funciones: 100%
Líneas: ~95%
Branches: ~90%
```

### Cantidad de tests:

- **test_payment_budget_validation.py**: 40+ tests
- **test_payment_advanced_scenarios.py**: 45+ tests
- **test_payment_integration_views.py**: 35+ tests
- **Total**: 120+ tests de validación de presupuesto y pagos

---

## 🎓 Lecciones Aprendidas de TC-52

### El Bug Ocurrió Porque:

1. ❌ La lógica de validación en edición calculaba mal el nuevo total
2. ❌ No restaba el monto VIEJO antes de sumar el monto NUEVO
3. ❌ Falta de tests que verificaran este escenario específico

### La Solución:

```python
# INCORRECTO (lo que hacía antes):
new_total = project.total_paid + new_amount  # ❌

# CORRECTO (lo que hace ahora):
new_total = (project.total_paid - old_amount) + new_amount  # ✅
```

### Por qué estos tests lo hubieran detectado:

El test `test_edit_payment_exceed_budget_should_fail` simula exactamente este escenario:
- Presupuesto: $10,000
- Pago actual: $5,000
- Editar a: $11,000
- Si la lógica es incorrecta, el test FALLA

---

## 🔗 Referencias

- **Ticket original**: TC-52
- **Componentes afectados**:
  - `apps/projects/models.py` - ProjectPayment, Project
  - `apps/projects/views.py` - PaymentCreateView, PaymentUpdateView
  - `apps/projects/finance_cache.py` - Caché invalidation
  
- **Validadores**:
  - `apps/core/validators.py` - validate_budget_amount, validate_payment_amount

---

## 📝 Notas Finales

Esta suite de tests está diseñada para:

1. **Validar que el bug TC-52 está realmente corregido**
2. **Encontrar nuevos bugs** en la validación de presupuesto
3. **Prevenir regresiones** en futuras ediciones
4. **Documentar el comportamiento esperado** del módulo

Recuerda: **Los tests NO deben pasar solo "porque sí"**. Deben ser tests que realmente encuentren problemas reales en el código.
