# SIMS - Quick Start Guide

## Prerequisites

- Python 3.8+
- PostgreSQL (or MySQL)
- Node.js and npm (for Tailwind CSS)

## Quick Setup (5 minutes)

### 1. Database Setup

**PostgreSQL:**
```sql
CREATE DATABASE sims_db;
```

Update `sims/settings.py` with your database credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sims_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Install and Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup groups and permissions
python manage.py setup_groups

# Setup Tailwind (requires Node.js)
python manage.py tailwind install
python manage.py tailwind build

# Run server
python manage.py runserver
```

### 3. Access the Application

- Visit: http://127.0.0.1:8000/
- Login with your superuser credentials
- You'll be redirected to the dashboard

## First Steps After Login

1. **Add Schools**: Go to Django Admin → Core → Schools
2. **Add Students**: Navigate to Students → Add Student
3. **Add Family Info**: Edit a student → Add Family Information
4. **Record Fees**: Go to Finance → Add Payment
5. **Add Insurance**: Go to Insurance → Add Insurance

## User Roles

After running `setup_groups`, you'll have three groups:

1. **Admin** - Full access
2. **Program Officer** - Can view/edit students, manage fees & insurance
3. **Data Entry** - Can add students, view records, manage fees & insurance

Assign users to groups via Django Admin → Authentication and Authorization → Groups

## Troubleshooting

### Tailwind CSS not working?
```bash
python manage.py tailwind install
python manage.py tailwind build
```

### Database connection error?
- Check your database credentials in `settings.py`
- Ensure PostgreSQL/MySQL is running
- Verify database exists

### Permission errors?
Run: `python manage.py setup_groups`

### Static files not loading?
```bash
python manage.py collectstatic
```

## Development Mode

For development with auto-reload:
```bash
python manage.py runserver
python manage.py tailwind start  # In another terminal
```

## Production Checklist

- [ ] Set `DEBUG = False`
- [ ] Update `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up proper database
- [ ] Configure static file serving
- [ ] Set up media file serving
- [ ] Use production WSGI server (Gunicorn)

