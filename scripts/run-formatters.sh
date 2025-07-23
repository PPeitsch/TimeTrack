#!/bin/bash

# Script to run isort, black, and mypy on the project
# Use: ./scripts/run-formatters.sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔍 Running code formatters and type checkers..."

# Run isort (con --skip-glob para cada directorio a ignorar)
echo "🔄 Running isort..."
python -m isort --profile black --skip-glob=".venv/*" --skip-glob="migrations/*" --skip-glob="instance/*" .

# Run black
echo "⬛ Running black..."
python -m black --exclude=".venv|migrations|instance" .

# Run mypy (types checking)
echo "📋 Running mypy..."
python -m mypy --ignore-missing-imports app

echo "✅ Formatting completed successfully!"
