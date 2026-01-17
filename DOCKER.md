# Docker Setup Guide for SIMS

This guide explains how to run SIMS using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

### 1. Clone and Navigate

```bash
cd sims
```

### 2. Create Environment File

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` and update the following:
- `SECRET_KEY`: Generate a secure secret key
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Add your domain(s)
- Database credentials (if different from defaults)

### 3. Build and Run

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Web Application**: http://localhost:80 (or http://localhost:8000 if nginx is disabled)
- **Django Admin**: http://localhost/admin

### 5. Create Superuser

```bash
# Option 1: Interactive
docker-compose exec web python manage.py createsuperuser

# Option 2: Automatic (set CREATE_SUPERUSER=true in .env)
```

## Docker Services

### 1. **db** - PostgreSQL Database
- Image: `postgres:15-alpine`
- Port: `5432`
- Data persisted in volume: `postgres_data`

### 2. **web** - Django Application
- Built from `Dockerfile`
- Port: `8000` (internal)
- Runs Gunicorn with 3 workers
- Auto-runs migrations on startup

### 3. **nginx** - Web Server (Optional)
- Image: `nginx:alpine`
- Port: `80`
- Serves static and media files
- Proxies requests to Django

## Docker Commands

### Development

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Execute commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py setup_groups
docker-compose exec web python manage.py shell
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U sims_user -d sims_db

# Backup database
docker-compose exec db pg_dump -U sims_user sims_db > backup.sql

# Restore database
docker-compose exec -T db psql -U sims_user sims_db < backup.sql
```

### Maintenance

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache

# View running containers
docker-compose ps

# Check resource usage
docker stats
```

## Environment Variables

Key environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | Django secret key (required) |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hostnames |
| `DB_NAME` | `sims_db` | Database name |
| `DB_USER` | `sims_user` | Database user |
| `DB_PASSWORD` | `sims_password` | Database password |
| `DB_HOST` | `db` | Database host (service name) |
| `DB_PORT` | `5432` | Database port |
| `CREATE_SUPERUSER` | `false` | Auto-create superuser |

## Production Deployment

### 1. Update `.env` for Production

```env
SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Use Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    environment:
      - DEBUG=False
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 sims.wsgi:application
```

### 3. Deploy

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. SSL/HTTPS

Add SSL certificates and update nginx configuration for HTTPS.

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python manage.py dbshell
```

### Static Files Not Loading

```bash
# Recollect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check nginx configuration
docker-compose exec nginx nginx -t
```

### Permission Issues

```bash
# Fix file permissions
docker-compose exec web chown -R www-data:www-data /app/media
docker-compose exec web chown -R www-data:www-data /app/staticfiles
```

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Tailwind CSS Issues

```bash
# Rebuild Tailwind
docker-compose exec web python manage.py tailwind build

# Install Tailwind dependencies
docker-compose exec web python manage.py tailwind install
```

## Volumes

Data is persisted in Docker volumes:

- `postgres_data`: Database data
- `static_volume`: Static files
- `media_volume`: Media uploads

To backup volumes:

```bash
docker run --rm -v sims_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Development vs Production

### Development
- `DEBUG=True`
- Hot reload enabled
- Single Gunicorn worker
- Development database

### Production
- `DEBUG=False`
- Multiple Gunicorn workers
- Production database
- SSL/HTTPS enabled
- Proper logging
- Monitoring setup

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Use strong database passwords
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor logs

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

