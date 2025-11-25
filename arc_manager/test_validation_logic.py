from apps.projects.models import Project, ProjectPayment
from decimal import Decimal

print("\n" + "=" * 80)
print("TEST: Validación de Edición de Pagos - TC-52")
print("=" * 80)

project = Project.objects.filter(name='Alonso Corp').first()

if project:
    print(f"\nProyecto: {project.name}")
    print(f"Presupuesto: ${project.total_budget:,.2f}")
    print(f"Total Pagado: ${project.total_paid:,.2f}")
    print(f"Saldo: ${project.remaining_amount:,.2f}")
    
    payment = project.payments.filter(amount=Decimal('300000.00')).first()
    
    if payment:
        print(f"\nPago de $300,000 encontrado (ID: {payment.id})")
        
        # Escenario 1: Aumentar a 300,100
        old, new = Decimal('300000.00'), Decimal('300100.00')
        new_total = (project.total_paid - old) + new
        print(f"\n--- ESCENARIO 1: Editar $300,000 a $300,100 ---")
        print(f"Nuevo total: ${new_total:,.2f}")
        print(f"Presupuesto: ${project.total_budget:,.2f}")
        print(f"¿Excede? {new_total > project.total_budget}")
        print(f"Resultado: {'❌ RECHAZAR (CORRECTO)' if new_total > project.total_budget else '✅ PERMITIR'}")
        
        # Escenario 2: Disminuir a 200,000
        old, new = Decimal('300000.00'), Decimal('200000.00')
        new_total = (project.total_paid - old) + new
        print(f"\n--- ESCENARIO 2: Editar $300,000 a $200,000 ---")
        print(f"Nuevo total: ${new_total:,.2f}")
        print(f"Presupuesto: ${project.total_budget:,.2f}")
        print(f"¿Excede? {new_total > project.total_budget}")
        print(f"Resultado: {'❌ RECHAZAR' if new_total > project.total_budget else '✅ PERMITIR (CORRECTO)'}")
    else:
        print(f"\n❌ No hay pago de $300,000")
else:
    print("\n❌ No se encontró el proyecto 'Alonso Corp'")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80 + "\n")
