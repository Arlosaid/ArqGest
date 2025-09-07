#!/usr/bin/env python
"""
Script para iniciar Celery Worker en Railway
"""
import os
import sys
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arc_manager.core.settings')

import django
django.setup()

from celery import Celery
from arc_manager.core.celery import app

if __name__ == '__main__':
    # Iniciar Celery worker
    app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--max-tasks-per-child=1000',
        '--time-limit=300',
        '--soft-time-limit=240'
    ])
