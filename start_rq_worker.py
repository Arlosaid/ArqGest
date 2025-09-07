#!/usr/bin/env python
"""
Script para iniciar RQ Worker en Railway
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

import django_rq

if __name__ == '__main__':
    # Obtener la cola por defecto
    queue = django_rq.get_queue('default')
    
    print(f"🚀 Iniciando RQ Worker para procesar emails...")
    print(f"📡 Conectado a Redis: {queue.connection}")
    print(f"📋 Cola: {queue.name}")
    
    # Iniciar el worker
    from rq import Worker
    
    worker = Worker([queue], connection=queue.connection)
    worker.work()
