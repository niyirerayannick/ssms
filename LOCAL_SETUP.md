# Local Development Setup (Windows)

Run SIMS on your local machine without Docker.

## Prerequisites

- Python 3.8+
- PostgreSQL (or use SQLite for quick start)
- Node.js (for Tailwind CSS)

## Quick Setup

### 1. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Database Setup

**Option A: PostgreSQL (Recommended)**
- Install PostgreSQL from https://www.postgresql.org/download/windows/
- Create database:
```sql
CREATE DATABASE sims_db;
CREATE USER sims_user WITH PASSWORD 'sims_password';
GRANT ALL PRIVILEGES ON DATABASE sims_db TO sims_user;
```

**Option B: SQLite (Quick Start)**
- Update `sims/settings.py` to use SQLite:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 4. Configure Settings

Create `.env` file or update `sims/settings.py` with your database credentials.

### 5. Run Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 6. Setup Groups

```powershell
python manage.py setup_groups
```

### 7. Create Superuser

```powershell
python manage.py createsuperuser
```

### 8. Setup Tailwind (Optional)

```powershell
python manage.py tailwind install
python manage.py tailwind build
```

### 9. Run Development Server

```powershell
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Using SQLite (Simplest Setup)

If you want to skip PostgreSQL setup:

1. Update `sims/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

2. Run migrations:
```powershell
python manage.py migrate
```

That's it! SQLite doesn't need a separate server.

## Troubleshooting

### Virtual Environment Issues

If `Activate.ps1` is blocked:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database Connection Error

- Check PostgreSQL is running
- Verify credentials in `settings.py`
- Or switch to SQLite for testing

### Port Already in Use

```powershell
python manage.py runserver 8001  # Use different port
```

## Development Workflow

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run server
python manage.py runserver

# In another terminal: Run Tailwind watch (for CSS changes)
python manage.py tailwind start
```

