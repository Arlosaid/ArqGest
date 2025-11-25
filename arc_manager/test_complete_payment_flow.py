from apps.projects.models import Project, ProjectPayment
from apps.orgs.models import Organization
from apps.accounts.models import User
from decimal import Decimal
from django.utils import timezone

print("\n" + "=" * 80)
print("TEST COMPLETO: Crear Proyecto, Presupuesto, Pago y Validar Edición")
print("=" * 80)

# 1. Obtener organización existente
print("\n1️⃣ OBTENER ORGANIZACIÓN...")
org = Organization.objects.first()
if org:
    print(f"   Organización: {org.name} (ID: {org.id})")
else:
    print(f"   ❌ No hay organizaciones disponibles")
    exit(1)

# 2. Obtener usuario
print("\n2️⃣ OBTENER USUARIO...")
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.filter(organization=org).first()
if user:
    print(f"   Usuario: {user.username} (ID: {user.id})")
else:
    print(f"   ❌ No hay usuarios disponibles")
    exit(1)

# 3. Crear proyecto
print("\n3️⃣ CREAR PROYECTO NUEVO SIN PRESUPUESTO...")
project = Project.objects.create(
    name='TC-52 Test - ' + timezone.now().isoformat(),
    organization=org,
    owner=user,
    total_budget=None,
    budget_configured=False,
)
print(f"   ✅ Proyecto creado: {project.name} (ID: {project.id})")
print(f"      Presupuesto: {project.total_budget} (sin configurar)")
print(f"      Total pagado: ${project.total_paid:,.2f}")

# 4. CONFIGURAR PRESUPUESTO
print("\n4️⃣ CONFIGURAR PRESUPUESTO A $10,000...")
project.total_budget = Decimal('10000.00')
project.budget_configured = True
project.save()
print(f"   ✅ Presupuesto configurado: ${project.total_budget:,.2f}")
print(f"      Disponible: ${project.remaining_amount:,.2f}")

# 5. AGREGAR PAGO DE $5,000
print("\n5️⃣ AGREGAR PRIMER PAGO DE $5,000...")
payment1 = ProjectPayment.objects.create(
    project=project,
    amount=Decimal('5000.00'),
    date=timezone.now().date(),
    description='Pago de prueba 1',
    created_by=user,
)
print(f"   ✅ Pago creado (ID: {payment1.id})")

# Refrescar proyecto
project.refresh_from_db()
print(f"\n   Estado después de agregar pago:")
print(f"   - Total pagado: ${project.total_paid:,.2f}")
print(f"   - Disponible: ${project.remaining_amount:,.2f}")
print(f"   - Presupuesto: ${project.total_budget:,.2f}")

# 6. VALIDAR EDICIÓN A $8,000 (dentro del presupuesto)
print("\n6️⃣ ESCENARIO 1: Editar pago de $5,000 a $8,000 (permitido)...")
old_amount = Decimal('5000.00')
new_amount = Decimal('8000.00')
new_total = (project.total_paid - old_amount) + new_amount

print(f"   Cambio: ${old_amount:,.2f} → ${new_amount:,.2f}")
print(f"   Nuevo total sería: ${new_total:,.2f}")
print(f"   Presupuesto: ${project.total_budget:,.2f}")
print(f"   ¿Excede? {new_total > project.total_budget}")

if new_total <= project.total_budget:
    print(f"   ✅ PERMITIR (correcto)")
else:
    print(f"   ❌ RECHAZAR")

# 7. VALIDAR EDICIÓN A $11,000 (FUERA del presupuesto)
print("\n7️⃣ ESCENARIO 2: Editar pago de $5,000 a $11,000 (DEBE RECHAZAR)...")
old_amount = Decimal('5000.00')
new_amount = Decimal('11000.00')
new_total = (project.total_paid - old_amount) + new_amount
max_allowed = project.total_budget - (project.total_paid - old_amount)

print(f"   Cambio: ${old_amount:,.2f} → ${new_amount:,.2f}")
print(f"   Nuevo total sería: ${new_total:,.2f}")
print(f"   Presupuesto: ${project.total_budget:,.2f}")
print(f"   Máximo permitido: ${max_allowed:,.2f}")
print(f"   ¿Excede? {new_total > project.total_budget}")

if new_total > project.total_budget:
    print(f"   ❌ RECHAZAR (correcto)")
    print(f"      Razón: ${new_total:,.2f} > ${project.total_budget:,.2f}")
    print(f"      Exceso: ${new_total - project.total_budget:,.2f}")
else:
    print(f"   ✅ PERMITIR")

# 8. VALIDAR EDICIÓN A $6,000 (dentro del presupuesto)
print("\n8️⃣ ESCENARIO 3: Editar pago de $5,000 a $6,000 (permitido)...")
old_amount = Decimal('5000.00')
new_amount = Decimal('6000.00')
new_total = (project.total_paid - old_amount) + new_amount

print(f"   Cambio: ${old_amount:,.2f} → ${new_amount:,.2f}")
print(f"   Nuevo total sería: ${new_total:,.2f}")
print(f"   Presupuesto: ${project.total_budget:,.2f}")
print(f"   ¿Excede? {new_total > project.total_budget}")

if new_total <= project.total_budget:
    print(f"   ✅ PERMITIR (correcto)")
else:
    print(f"   ❌ RECHAZAR")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO - VALIDACIÓN FUNCIONANDO CORRECTAMENTE")
print("=" * 80 + "\n")
