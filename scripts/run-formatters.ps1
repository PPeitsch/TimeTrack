# Script to run isort, black, and mypy on Windows
# Use: .\scripts\run-formatters.ps1

Write-Host "Running code formatters and type checkers..." -ForegroundColor Cyan

# Run isort with skip-glob
Write-Host "Running isort..." -ForegroundColor Yellow
python -m isort --profile black --skip-glob=".venv/*" --skip-glob="migrations/*" --skip-glob="instance/*" .

# Run black
Write-Host "⬛ Running black..." -ForegroundColor Yellow
python -m black --exclude=".venv|migrations|instance" .

# Run mypy (types checking)
Write-Host "Running mypy..." -ForegroundColor Yellow
python -m mypy --ignore-missing-imports app

Write-Host "Formatting completed successfully!" -ForegroundColor Green
