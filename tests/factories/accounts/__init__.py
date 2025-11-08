"""
Factories del módulo accounts.

Importar desde aquí para mantener compatibilidad:
    from tests.factories.accounts import UserFactory, SuperUserFactory
"""
from .account_factories import (
    UserFactory,
    SuperUserFactory,
    OrgAdminFactory,
    InactiveUserFactory,
)

__all__ = [
    'UserFactory',
    'SuperUserFactory', 
    'OrgAdminFactory',
    'InactiveUserFactory',
]
