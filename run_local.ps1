# Quick local run script for SIMS
Write-Host "Starting SIMS locally..." -ForegroundColor Cyan

# Activate virtual environment if not already active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
    } else {
        Write-Host "Error: Virtual environment not found. Run: python -m venv venv" -ForegroundColor Red
        exit 1
    }
}

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$djangoInstalled = python -c "import django" 2>$null
if (-not $djangoInstalled) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Run migrations (silently)
Write-Host "Checking database..." -ForegroundColor Yellow
python manage.py migrate --run-syncdb 2>$null | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Django development server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Visit: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start server
python manage.py runserver

