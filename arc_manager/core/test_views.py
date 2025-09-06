"""
Vistas de prueba para testear los handlers de error.
Solo disponibles cuando DEBUG=True.
"""
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings


def test_400(request):
    """Simula un error 400 para testing."""
    if not settings.DEBUG:
        raise Http404("Not available in production")
    return HttpResponseBadRequest("Test 400 error")


def test_403(request):
    """Simula un error 403 para testing."""
    if not settings.DEBUG:
        raise Http404("Not available in production")
    return HttpResponseForbidden("Test 403 error")


def test_404(request):
    """Simula un error 404 para testing."""
    if not settings.DEBUG:
        raise Http404("Not available in production")
    raise Http404("Test 404 error")


def test_500(request):
    """Simula un error 500 para testing."""
    if not settings.DEBUG:
        raise Http404("Not available in production")
    raise Exception("Test 500 error")
