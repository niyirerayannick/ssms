# PowerShell script to set up SIMS locally
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SIMS - Local Development Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create migrations
Write-Host ""
Write-Host "Creating database migrations..." -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Migration creation failed (may already exist)" -ForegroundColor Yellow
}

# Run migrations
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Migration failed. Check your database configuration." -ForegroundColor Red
    Write-Host "Tip: You can use SQLite by uncommenting it in sims/settings.py" -ForegroundColor Yellow
}

# Setup groups
Write-Host ""
Write-Host "Setting up user groups and permissions..." -ForegroundColor Yellow
python manage.py setup_groups
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Group setup failed (may already exist)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create superuser: python manage.py createsuperuser" -ForegroundColor White
Write-Host "2. (Optional) Setup Tailwind: python manage.py tailwind install" -ForegroundColor White
Write-Host "3. Run server: python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Visit: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host ""

