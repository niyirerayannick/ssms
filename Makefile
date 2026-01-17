.PHONY: help build up down restart logs shell migrate createsuperuser setup test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs
	docker-compose logs -f

logs-web: ## View web service logs
	docker-compose logs -f web

logs-db: ## View database logs
	docker-compose logs -f db

shell: ## Open Django shell
	docker-compose exec web python manage.py shell

bash: ## Open bash in web container
	docker-compose exec web bash

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create migrations
	docker-compose exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	docker-compose exec web python manage.py createsuperuser

setup-groups: ## Setup user groups and permissions
	docker-compose exec web python manage.py setup_groups

collectstatic: ## Collect static files
	docker-compose exec web python manage.py collectstatic --noinput

tailwind-build: ## Build Tailwind CSS
	docker-compose exec web python manage.py tailwind build

setup: ## Initial setup (migrations, groups, static files)
	@echo "Running initial setup..."
	docker-compose exec web python manage.py migrate
	docker-compose exec web python manage.py setup_groups
	docker-compose exec web python manage.py collectstatic --noinput
	docker-compose exec web python manage.py tailwind build
	@echo "Setup complete!"

test: ## Run tests
	docker-compose exec web python manage.py test

clean: ## Remove containers, volumes, and images
	docker-compose down -v
	docker system prune -f

rebuild: ## Rebuild everything from scratch
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 10
	$(MAKE) setup

dev: ## Start in development mode
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U sims_user -d sims_db

backup-db: ## Backup database
	docker-compose exec db pg_dump -U sims_user sims_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up!"

restore-db: ## Restore database (usage: make restore-db FILE=backup.sql)
	docker-compose exec -T db psql -U sims_user sims_db < $(FILE)
	@echo "Database restored!"

