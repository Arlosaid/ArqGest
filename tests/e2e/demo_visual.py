"""
DEMO VISUAL - Ejecuta esto para VER el navegador en acción

Uso:
    python tests/e2e/demo_visual.py

Este script abre un navegador VISIBLE y navega por tu app.
"""
from playwright.sync_api import sync_playwright
import time


def demo():
    print("🚀 Iniciando demostración visual de Playwright...")
    print("   Verás un navegador Chrome abrirse automáticamente\n")
    
    with sync_playwright() as p:
        # Abre Chrome VISIBLE (no headless)
        browser = p.chromium.launch(
            headless=False,  # ← Esto hace que VEAS el navegador
            slow_mo=500      # ← Hace cada acción más lenta para que veas
        )
        
        page = browser.new_page()
        
        # === NAVEGACIÓN ===
        print("📍 Navegando a http://localhost:8000...")
        page.goto("http://localhost:8000")
        time.sleep(1)
        
        # === PÁGINA DE LOGIN ===
        print("📍 Yendo a página de login...")
        page.goto("http://localhost:8000/accounts/login/")
        time.sleep(2)
        
        # Highlight del formulario
        page.evaluate("""
            document.querySelector('form').style.border = '3px solid red';
        """)
        print("   ⬆️ Formulario marcado en ROJO")
        time.sleep(1)
        
        # === LLENAR CAMPOS ===
        print("📝 Escribiendo en campos de login...")
        
        # Usuario
        username_field = page.locator('input[name="username"], input[name="login"]').first
        username_field.click()
        time.sleep(0.3)
        username_field.fill("demo@ejemplo.com")
        
        # Password
        password_field = page.locator('input[name="password"]').first
        password_field.click()
        time.sleep(0.3)
        password_field.fill("password123")
        
        print("   ✅ Campos llenados automáticamente")
        time.sleep(2)
        
        # === PÁGINA DE ADMIN ===
        print("\n📍 Navegando al Admin de Django...")
        page.goto("http://localhost:8000/admin/")
        time.sleep(2)
        
        # === SCREENSHOT ===
        screenshot_path = "tests/e2e/screenshots/demo_visual.png"
        page.screenshot(path=screenshot_path)
        print(f"\n📸 Screenshot guardado: {screenshot_path}")
        
        # Esperar para que veas
        print("\n⏳ Navegador abierto por 5 segundos más...")
        time.sleep(5)
        
        browser.close()
        print("\n✅ Demo completada!")
        print("   Esto es lo que hacen los tests E2E, pero más rápido y sin interfaz visible.")


if __name__ == "__main__":
    demo()
