"""
Custom AXES handler - DESHABILITADO
Los logs de login se manejan directamente en accounts/views.py
para evitar duplicación y tener mejor control sobre la información mostrada.
"""
from axes.handlers.database import AxesDatabaseHandler


class CustomAxesHandler(AxesDatabaseHandler):
    """
    Handler que usa el comportamiento por defecto de AXES.
    El logging se maneja en accounts/views.py para tener logs claros y útiles.
    """
    pass
