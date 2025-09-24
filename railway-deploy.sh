#!/bin/bash
# Script para desplegar en Railway evitando problemas de Docker Hub

echo "🚀 Desplegando en Railway..."

# Configurar variables de entorno
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Usar Dockerfile específico
cp Dockerfile.python Dockerfile

# Desplegar con Railway CLI
railway up --detach

echo "✅ Despliegue completado"
