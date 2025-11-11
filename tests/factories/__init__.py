"""
Factories para tests - Importación facilitada.

Estructura:
- factories/accounts/  → UserFactory, SuperUserFactory, etc.
- factories/orgs/      → OrganizationFactory
- factories/plans/     → PlanFactory, SubscriptionFactory (futuro)
- factories/projects/  → ProjectFactory, TransactionFactory (futuro)
- factories/files/     → FileUploadFactory (futuro)

Uso:
    # Opción 1: Importar desde el módulo específico
    from tests.factories.accounts import UserFactory
    
    # Opción 2: Importar desde este archivo (más corto)
    from tests.factories import UserFactory
"""

# Re-exportar todas las factories para facilitar importación
from .accounts import (
    UserFactory,
    SuperUserFactory,
    OrgAdminFactory,
    InactiveUserFactory,
)

from .orgs import (
    OrganizationFactory,
    InactiveOrganizationFactory,
    FounderOrganizationFactory,
    OrganizationWithExtraStorageFactory,
    ClientFactory,
    InactiveClientFactory,
)

from .plans import (
    PlanFactory,
    TrialPlanFactory,
    BasicPlanFactory,
    SubscriptionFactory,
    TrialSubscriptionFactory,
    PaymentFactory,
)

from .projects import (
    ProjectFactory,
    ActiveProjectFactory,
    ArchivedProjectFactory,
    CompletedProjectFactory,
    PhaseFactory,
    PendingPhaseFactory,
    InProgressPhaseFactory,
    CompletedPhaseFactory,
    TaskFactory,
    TodoTaskFactory,
    InProgressTaskFactory,
    DoneTaskFactory,
    PausedTaskFactory,
    HighPriorityTaskFactory,
    ProjectPaymentFactory,
    PhaseTemplateFactory,
)

__all__ = [
    # Accounts
    'UserFactory',
    'SuperUserFactory',
    'OrgAdminFactory',
    'InactiveUserFactory',
    # Orgs
    'OrganizationFactory',
    'InactiveOrganizationFactory',
    'FounderOrganizationFactory',
    'OrganizationWithExtraStorageFactory',
    'ClientFactory',
    'InactiveClientFactory',
    # Plans
    'PlanFactory',
    'TrialPlanFactory',
    'BasicPlanFactory',
    'SubscriptionFactory',
    'TrialSubscriptionFactory',
    'PaymentFactory',
    # Projects
    'ProjectFactory',
    'ActiveProjectFactory',
    'ArchivedProjectFactory',
    'CompletedProjectFactory',
    'PhaseFactory',
    'PendingPhaseFactory',
    'InProgressPhaseFactory',
    'CompletedPhaseFactory',
    'TaskFactory',
    'TodoTaskFactory',
    'InProgressTaskFactory',
    'DoneTaskFactory',
    'PausedTaskFactory',
    'HighPriorityTaskFactory',
    'ProjectPaymentFactory',
    'PhaseTemplateFactory',
]
