# 🧪 Tests - ARC Manager

Suite de tests automatizados robustos para ARC Manager.

**Estado:** ~1261 tests implementados | ~78% cobertura | ~99% passing

---

## 🚀 INICIO RÁPIDO

### Para Continuar con la Implementación

```bash
# 1. Lee el documento maestro (OBLIGATORIO)
cat docs/TESTS_MASTER_GUIDE.md

# 2. O usa el índice para navegar
cat docs/TESTS_INDEX.md
```

### Para Ejecutar Tests

```bash
# Todos los tests
docker-compose exec web pytest tests/ -v

# Un módulo específico
docker-compose exec web pytest tests/projects/ -v

# Con cobertura
docker-compose exec web pytest --cov=apps --cov-report=html
```

---

## 📚 DOCUMENTACIÓN

### ⭐ Documentos Principales

1. **[TESTS_MASTER_GUIDE.md](../docs/TESTS_MASTER_GUIDE.md)**  
   📖 Guía completa con TODO el contexto. **LEE ESTE PRIMERO.**
   
2. **[TESTS_INDEX.md](../docs/TESTS_INDEX.md)**  
   📑 Índice de toda la documentación de tests.
   
3. **[TESTS_NEXT_STEPS.md](../docs/TESTS_NEXT_STEPS.md)**  
   🎯 Resumen del próximo paso (módulo FILES).
   
4. **[TESTS_IMPLEMENTATION_SUMMARY.md](../docs/TESTS_IMPLEMENTATION_SUMMARY.md)**  
   📊 Resumen detallado de todo lo implementado.

---

## 📦 ESTADO POR MÓDULO

```
✅ ACCOUNTS  ( 87 tests) - 100% completo
✅ ORGS      (~385 tests) -  90% completo  
✅ PLANS     (~378 tests) - 100% completo
✅ PROJECTS  (~270 tests) -  95% completo
✅ FILES     (141 tests) - 100% completo ← RECIÉN COMPLETADO
⏳ USERS     (  0 tests) -   0% ← SIGUIENTE
⏳ MAIN      (  0 tests) -   0%
```

---

## 🗂️ ESTRUCTURA

```
tests/
├── README.md                    # ← Estás aquí
│
├── conftest.py                  # Configuración global
├── pytest.ini                   # Config de pytest
│
├── factories/                   # Factories para tests
│   ├── __init__.py
│   ├── accounts/
│   ├── orgs/
│   ├── plans/
│   └── projects/                # ✅ NUEVO
│
├── accounts/                    # ✅ 87 tests
├── orgs/                        # ✅ ~385 tests
├── plans/                       # ✅ ~378 tests
├── projects/                    # ✅ ~270 tests
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_project_models.py
│   │   ├── test_phase_models.py
│   │   ├── test_task_models.py
│   │   └── test_payment_models.py
│   └── admin/
│
├── files/                       # ✅ 141 tests (NUEVO)
│   ├── conftest.py
│   ├── security/
│   │   └── test_file_security.py     # 41 tests
│   └── unit/
│       ├── test_file_models.py       # 47 tests
│       ├── test_file_manager.py      # 30 tests
│       └── test_file_storage.py      # 23 tests
├── users/                       # ⏳ Pendiente
└── main/                        # ⏳ Pendiente
```

---

## 🎯 PRÓXIMO PASO

**Módulo USERS** (Importante - Gestión de usuarios)

Prioridad media. Sistema de usuarios, permisos y roles.

Ver instrucciones en documentación:
- `tests/docs/CONTINUAR_AQUI.md`

---

## 🔧 COMANDOS ÚTILES

```bash
# Ejecutar tests de un archivo específico
docker-compose exec web pytest tests/projects/unit/test_project_models.py -v

# Ejecutar un test específico
docker-compose exec web pytest tests/projects/unit/test_project_models.py::TestProjectCreation::test_project_creation_with_factory -v

# Ejecutar con output visible (para debug)
docker-compose exec web pytest tests/projects/ -v -s

# Ejecutar solo tests de seguridad
docker-compose exec web pytest -m security -v

# Ver cobertura
docker-compose exec web pytest --cov=apps.projects --cov-report=term-missing

# Generar reporte HTML de cobertura
docker-compose exec web pytest --cov=apps --cov-report=html
# Ver en: htmlcov/index.html
```

---

## 📖 PARA EMPEZAR

### Si Nunca Has Visto Este Proyecto

1. Lee `docs/TESTS_INDEX.md` para entender la organización
2. Lee `docs/TESTS_MASTER_GUIDE.md` para el contexto completo
3. Mira `tests/projects/unit/` para ver ejemplos recientes
4. Empieza con el módulo FILES siguiendo la guía

### Si Ya Conoces el Proyecto

1. Lee `docs/TESTS_NEXT_STEPS.md` para ver qué sigue
2. Usa el prompt en `TESTS_MASTER_GUIDE.md`
3. Sigue los patrones de `tests/projects/`

---

## 🏆 CARACTERÍSTICAS

### ✅ Tests Robustos
- No son superficiales
- Detectan bugs reales
- Edge cases cubiertos
- Validaciones exhaustivas

### ✅ Bien Organizados
- Estructura clara por módulo
- Factories reutilizables
- Fixtures para setup común
- Documentación inline

### ✅ Mantenibles
- Nombres descriptivos
- Comentarios explicativos
- Patrones consistentes
- Fáciles de entender

### ✅ Completos
- Creación y validaciones
- Relaciones y CASCADE
- Propiedades y métodos
- Security y edge cases

---

## 📊 ESTADÍSTICAS

- **Tests Totales:** ~1261
- **Archivos de Test:** ~44+
- **Factories:** ~55+
- **Cobertura:** ~78%
- **Passing Rate:** ~99%
- **Bugs Encontrados:** 6 críticos (arreglados), 8+ potenciales

---

## 🐛 BUGS ENCONTRADOS

### Críticos (Arreglados) ✅
1. Superusuarios limitados por límite de organización (Orgs)
2. Path Traversal en uploads (`../../../etc/passwd`) (Files)
3. Ejecutables disfrazados como PDFs no detectados (Files)
4. Cross-organization file uploads sin validación (Files)
5. Null bytes en filenames no removidos (Files)
6. Nombres de archivo muy largos sin truncar (Files)

### Potenciales (Documentados) ⚠️
- No hay validación start_date < end_date (Project/Phase)
- Cliente puede ser de diferente organización (Project)
- Pagos pueden tener monto negativo/cero (ProjectPayment)
- Pagos pueden tener fechas futuras (ProjectPayment)
- No hay constraint de unicidad (project, order) en Phase

Ver más en: `tests/docs/`

---

## 💡 TIPS

### Para Escribir Buenos Tests
- Nombres descriptivos que expliquen la intención
- Un concepto por test (no múltiples validaciones)
- Comentarios para bugs potenciales y edge cases
- Assertions claras con mensajes de error

### Para Debuggear
- Usa `-s` flag para ver prints
- Agrega `import pdb; pdb.set_trace()` para breakpoints
- Ejecuta solo el test que falla
- Revisa los fixtures y factories

### Para Mantener Calidad
- Ejecuta tests antes de commit
- Mantén coverage > 90% en nuevo código
- Documenta bugs encontrados
- Actualiza documentación

---

## 🔗 REFERENCIAS

- [Pytest Docs](https://docs.pytest.org/)
- [Factory Boy Docs](https://factoryboy.readthedocs.io/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)

---

## 📞 SOPORTE

Para preguntas o dudas:
1. Lee la documentación en `docs/`
2. Revisa ejemplos en módulos completados
3. Busca patrones similares en otros tests

---

**Última actualización:** 11 de Noviembre, 2025  
**Versión:** 1.1  
**Próximo módulo:** USERS
