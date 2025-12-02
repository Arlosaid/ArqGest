"""
E2E Tests - Pruebas de navegador simulando usuarios reales

Estos tests usan Playwright para automatizar un navegador real y simular
flujos completos de usuario: login, crear proyectos, tareas, pagos, etc.

Para ejecutar:
    pytest tests/e2e/ -v -m e2e

Para ver el navegador mientras corre:
    pytest tests/e2e/ -v --headed

Para ejecutar un test específico:
    pytest tests/e2e/test_login.py -v
"""
