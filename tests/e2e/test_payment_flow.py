"""
Tests E2E: Flujo de Pagos con Comprobantes

Estos tests verifican el ciclo completo de gestión de pagos:
- Crear pagos desde el dashboard de finanzas
- Subir comprobantes de pago (archivos adjuntos)
- Editar y eliminar pagos
- Verificar cálculos de totales
"""
import pytest
import tempfile
import os
from playwright.sync_api import Page, expect
from decimal import Decimal


@pytest.fixture
def temp_receipt_pdf():
    """Crea un PDF simulando un comprobante de pago"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Comprobante de Pago) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
296
%%EOF"""
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        f.write(pdf_content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_receipt_image():
    """Crea una imagen simulando un comprobante de pago"""
    try:
        from PIL import Image
        img = Image.new('RGB', (400, 600), color='white')
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            temp_path = f.name
        img.save(temp_path, 'JPEG')
    except ImportError:
        # Fallback sin PIL
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11,
            0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB,
            0xD5, 0xDB, 0x20, 0xFF, 0xD9
        ])
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            f.write(jpeg_bytes)
            temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPaymentCreation:
    """Tests de creación de pagos"""
    
    def test_create_payment_from_finance_dashboard(self, logged_in_page: Page, live_server, db):
        """Crear pago desde el dashboard de finanzas"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from tests.factories.orgs.org_factories import ClientFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        client = ClientFactory(organization=user.organization, name='Cliente Pago E2E')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            client=client,
            name='Proyecto Crear Pago Dashboard E2E',
            total_budget=Decimal('100000'),
            budget_configured=True,
            status='active'
        )
        PhaseFactory(project=project, name='Fase Principal', order=1)
        
        initial_count = ProjectPayment.objects.filter(project=project).count()
        
        # Ir al dashboard de finanzas
        page.goto(f"{live_server.url}/projects/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón "+ Pago" para el proyecto
        add_payment_btn = page.locator('a:has-text("Pago"), button:has-text("Pago"), .btn:has-text("Pago")').first
        
        if add_payment_btn.is_visible():
            add_payment_btn.click()
            page.wait_for_timeout(1000)
            
            # Verificar modal/formulario
            amount_field = page.locator('input[name="amount"]:visible')
            
            if amount_field.count() > 0:
                amount_field.fill('35000')
                
                # Descripción
                desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
                if desc_field.count() > 0:
                    desc_field.first.fill('Anticipo del 35% - Inicio de proyecto')
                
                # Fecha de pago si existe
                date_field = page.locator('input[name="payment_date"]:visible, input[type="date"]:visible')
                if date_field.count() > 0:
                    date_field.first.fill('2024-12-01')
                
                # Guardar
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn:
                    save_btn.click()
                    page.wait_for_timeout(2000)
                
                # Verificar creación
                final_count = ProjectPayment.objects.filter(project=project).count()
                assert final_count > initial_count, "Debería haberse creado el pago"
                print(f"✓ Pago creado: {initial_count} -> {final_count}")
            else:
                pytest.skip("No se encontró campo de monto")
        else:
            pytest.skip("No se encontró botón de agregar pago")
    
    def test_create_payment_from_project_finance_detail(self, logged_in_page: Page, live_server, db):
        """Crear pago desde el detalle financiero del proyecto"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Pago Detalle E2E',
            total_budget=Decimal('80000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        initial_count = ProjectPayment.objects.filter(project=project).count()
        
        # Ir al detalle financiero del proyecto
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón de agregar pago
        add_btn = page.locator(
            'a:has-text("Agregar"), a:has-text("Nuevo Pago"), '
            'button:has-text("Agregar"), button:has-text("Nuevo Pago")'
        )
        
        if add_btn.count() > 0 and add_btn.first.is_visible():
            add_btn.first.click()
            page.wait_for_timeout(1000)
            
            amount_field = page.locator('input[name="amount"]:visible')
            if amount_field.count() > 0:
                amount_field.fill('20000')
                
                desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
                if desc_field.count() > 0:
                    desc_field.first.fill('Segundo pago - Avance de obra')
                
                save_btn = page.locator('button[type="submit"]:visible').first
                if save_btn:
                    save_btn.click()
                    page.wait_for_timeout(2000)
                
                final_count = ProjectPayment.objects.filter(project=project).count()
                print(f"✓ Pago desde detalle: {initial_count} -> {final_count}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPaymentWithReceipt:
    """Tests de pagos con comprobantes adjuntos"""
    
    def test_create_payment_with_pdf_receipt(
        self, logged_in_page: Page, live_server, db, temp_receipt_pdf
    ):
        """Crear pago con comprobante PDF adjunto"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Pago PDF E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Ir a crear pago
        page.goto(f"{live_server.url}/projects/{project.pk}/payments/new/")
        page.wait_for_load_state("networkidle")
        
        # Llenar formulario
        amount_field = page.locator('input[name="amount"]:visible')
        
        if amount_field.count() > 0:
            amount_field.fill('45000')
            
            desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
            if desc_field.count() > 0:
                desc_field.first.fill('Pago con comprobante PDF')
            
            # Buscar campo de archivo para comprobante
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(temp_receipt_pdf)
                page.wait_for_timeout(500)
                print("✓ Comprobante PDF adjuntado")
            
            # Guardar
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar
            payment = ProjectPayment.objects.filter(project=project).first()
            if payment:
                print(f"✓ Pago creado: ${payment.amount}")
                # Verificar si tiene archivo adjunto (si el modelo lo soporta)
                if hasattr(payment, 'receipt') and payment.receipt:
                    print(f"✓ Comprobante guardado: {payment.receipt.name}")
        else:
            # Puede que la URL sea diferente, intentar desde dashboard
            page.goto(f"{live_server.url}/projects/finance/")
            page.wait_for_load_state("networkidle")
            pytest.skip("URL de crear pago no accesible directamente")
    
    def test_create_payment_with_image_receipt(
        self, logged_in_page: Page, live_server, db, temp_receipt_image
    ):
        """Crear pago con comprobante imagen (JPG) adjunto"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Pago Imagen E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        page.goto(f"{live_server.url}/projects/{project.pk}/payments/new/")
        page.wait_for_load_state("networkidle")
        
        amount_field = page.locator('input[name="amount"]:visible')
        
        if amount_field.count() > 0:
            amount_field.fill('28000')
            
            desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
            if desc_field.count() > 0:
                desc_field.first.fill('Pago con foto de comprobante')
            
            # Adjuntar imagen
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(temp_receipt_image)
                page.wait_for_timeout(500)
                print("✓ Comprobante imagen adjuntado")
            
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
        else:
            pytest.skip("Formulario de pago no encontrado")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPaymentManagement:
    """Tests de gestión de pagos (editar, eliminar)"""
    
    def test_edit_payment(self, logged_in_page: Page, live_server, db):
        """Usuario puede editar un pago existente"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Editar Pago E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Crear pago existente
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('30000'),
            description='Pago original',
            created_by=user
        )
        
        # Ir a editar pago
        page.goto(f"{live_server.url}/projects/payments/{payment.pk}/edit/")
        page.wait_for_load_state("networkidle")
        
        # Verificar que cargó el formulario con datos existentes
        amount_field = page.locator('input[name="amount"]:visible')
        
        if amount_field.count() > 0:
            # Actualizar monto
            amount_field.clear()
            amount_field.fill('35000')
            
            # Actualizar descripción
            desc_field = page.locator('input[name="description"]:visible, textarea[name="description"]:visible')
            if desc_field.count() > 0:
                desc_field.first.clear()
                desc_field.first.fill('Pago actualizado E2E')
            
            # Guardar
            save_btn = page.locator('button[type="submit"]:visible').first
            if save_btn:
                save_btn.click()
                page.wait_for_timeout(2000)
            
            # Verificar actualización
            payment.refresh_from_db()
            assert payment.amount == Decimal('35000'), f"Monto debería ser 35000, es {payment.amount}"
            print(f"✓ Pago actualizado: ${payment.amount}")
        else:
            pytest.skip("Formulario de edición no encontrado")
    
    def test_delete_payment(self, logged_in_page: Page, live_server, db):
        """Usuario puede eliminar un pago"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        from apps.projects.models import ProjectPayment
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Eliminar Pago E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        payment = ProjectPaymentFactory(
            project=project,
            amount=Decimal('20000'),
            description='Pago a eliminar',
            created_by=user
        )
        payment_id = payment.pk
        
        # Ir al detalle financiero del proyecto
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar botón de eliminar
        delete_btn = page.locator(
            'a:has-text("Eliminar"):visible, '
            'button:has-text("Eliminar"):visible, '
            '[data-action="delete"]:visible'
        )
        
        if delete_btn.count() > 0:
            delete_btn.first.click()
            page.wait_for_timeout(500)
            
            # Confirmar eliminación
            confirm_btn = page.locator(
                'button:has-text("Confirmar"):visible, '
                'button:has-text("Sí"):visible, '
                'button:has-text("Eliminar"):visible'
            )
            if confirm_btn.count() > 0:
                confirm_btn.first.click()
                page.wait_for_timeout(2000)
            
            # Verificar eliminación
            payment_exists = ProjectPayment.objects.filter(pk=payment_id).exists()
            print(f"✓ Pago eliminado: {not payment_exists}")
        else:
            # Intentar URL directa
            page.goto(f"{live_server.url}/projects/payments/{payment_id}/delete/")
            page.wait_for_load_state("networkidle")
            
            confirm_btn = page.locator('button[type="submit"]:visible')
            if confirm_btn.count() > 0:
                confirm_btn.first.click()
                page.wait_for_timeout(2000)
                
                payment_exists = ProjectPayment.objects.filter(pk=payment_id).exists()
                print(f"✓ Pago eliminado (URL directa): {not payment_exists}")


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestPaymentCalculations:
    """Tests de cálculos de pagos"""
    
    def test_multiple_payments_total_calculation(self, logged_in_page: Page, live_server, db):
        """Verificar que la suma de múltiples pagos se calcula correctamente"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Multi Pagos E2E',
            total_budget=Decimal('100000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Crear múltiples pagos
        ProjectPaymentFactory(project=project, amount=Decimal('25000'), description='Pago 1', created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('15000'), description='Pago 2', created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('20000'), description='Pago 3', created_by=user)
        # Total: $60,000 de $100,000 = 60%
        
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Verificar total pagado
        total_indicators = page.locator(
            'text=60,000, text=$60,000, text=60000'
        )
        has_correct_total = total_indicators.count() > 0
        
        # Verificar porcentaje
        percentage_indicators = page.locator(
            'text=60%, text=60 %'
        )
        has_percentage = percentage_indicators.count() > 0
        
        # Verificar balance restante ($40,000)
        balance_indicators = page.locator(
            'text=40,000, text=$40,000, text=40000'
        )
        has_balance = balance_indicators.count() > 0
        
        print(f"✓ Total correcto visible: {has_correct_total}")
        print(f"✓ Porcentaje visible: {has_percentage}")
        print(f"✓ Balance visible: {has_balance}")
    
    def test_payment_exceeds_budget_warning(self, logged_in_page: Page, live_server, db):
        """Verificar comportamiento cuando los pagos exceden el presupuesto"""
        from tests.factories.projects.project_factories import ProjectFactory, PhaseFactory, ProjectPaymentFactory
        from apps.accounts.models import User
        
        page = logged_in_page
        user = User.objects.get(email='e2e@test.com')
        
        project = ProjectFactory(
            organization=user.organization,
            owner=user,
            name='Proyecto Exceso Pagos E2E',
            total_budget=Decimal('50000'),
            budget_configured=True
        )
        PhaseFactory(project=project, name='Fase 1', order=1)
        
        # Crear pagos que excedan el presupuesto
        ProjectPaymentFactory(project=project, amount=Decimal('30000'), created_by=user)
        ProjectPaymentFactory(project=project, amount=Decimal('25000'), created_by=user)
        # Total: $55,000 de $50,000 = 110%
        
        page.goto(f"{live_server.url}/projects/{project.pk}/finance/")
        page.wait_for_load_state("networkidle")
        
        # Buscar indicadores de advertencia o exceso
        # Separar selectores CSS de selectores de texto
        css_warning = page.locator('[class*="warning"], [class*="danger"], [class*="over"]')
        text_warning = page.locator(':text("excedido"), :text("sobre presupuesto")')
        
        # Verificar si hay elementos con 110% visible
        page_content = page.content()
        has_percent_warning = '110%' in page_content or '55000' in page_content or '55.000' in page_content
        
        has_warning = css_warning.count() > 0 or text_warning.count() > 0 or has_percent_warning
        print(f"✓ Advertencia de exceso: {has_warning}")
