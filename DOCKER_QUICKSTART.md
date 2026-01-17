# Docker Quick Start

## 🚀 Get Started in 3 Steps

### 1. Setup Environment
```bash
cp env.example .env
# Edit .env and set SECRET_KEY
```

### 2. Start Services
```bash
docker-compose up -d --build
```

### 3. Initialize
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_groups
docker-compose exec web python manage.py createsuperuser
```

**Done!** Visit http://localhost:80

---

## 📋 Common Commands

### Using Makefile (Easier)
```bash
make build          # Build images
make up             # Start services
make down           # Stop services
make logs           # View logs
make shell          # Django shell
make migrate        # Run migrations
make createsuperuser # Create admin user
make setup          # Full setup (migrate + groups + static)
```

### Using Docker Compose Directly
```bash
# Start/Stop
docker-compose up -d              # Start in background
docker-compose down               # Stop
docker-compose restart           # Restart

# Logs
docker-compose logs -f web        # Web logs
docker-compose logs -f db         # Database logs

# Django Commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Database
docker-compose exec db psql -U sims_user -d sims_db
```

---

## 🔧 Development Mode

For development with hot reload:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This uses Django's runserver instead of Gunicorn.

---

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose down -v    # Remove volumes
docker-compose build --no-cache
docker-compose up -d
```

### Database connection error
```bash
docker-compose logs db    # Check database logs
docker-compose ps         # Check if db is running
```

### Static files not loading
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Permission errors
```bash
docker-compose exec web python manage.py setup_groups
```

---

## 📦 Services

- **web** (port 8000): Django application
- **db** (port 5432): PostgreSQL database
- **nginx** (port 80): Web server (production)

---

## 🔐 Default Credentials

If `CREATE_SUPERUSER=true` in `.env`:
- Username: `admin`
- Password: `admin123`

**⚠️ Change this in production!**

---

## 📚 More Information

See [DOCKER.md](DOCKER.md) for complete documentation.

