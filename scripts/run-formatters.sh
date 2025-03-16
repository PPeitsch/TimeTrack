#!/bin/bash

# Script para ejecutar isort, black y mypy en el proyecto
# Uso: ./scripts/run-formatters.sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔍 Running code formatters and type checkers..."

# Define directories to skip
SKIP_DIRS=".venv,migrations,instance"

# Run isort
echo "🔄 Running isort..."
python -m isort --profile black --skip $SKIP_DIRS .

# Run black
echo "⬛ Running black..."
python -m black .

# Run mypy (types checking)
echo "📋 Running mypy..."
python -m mypy --ignore-missing-imports app

echo "✅ Formateo completado exitosamente!"