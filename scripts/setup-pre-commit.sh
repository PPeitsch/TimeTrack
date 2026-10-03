#!/bin/bash

# Script para configurar pre-commit hooks
# Uso: ./scripts/setup-pre-commit.sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "Setting up pre-commit hooks..."

# Ensure we have the necessary packages
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

echo "Pre-commit hooks installed successfully!"
echo "Now your code will be automatically checked and formatted before each commit."
