# SIMS - Sponsorship Information Management System

A Django-based web application for managing student sponsorship information for SolidAct Foundation.

## Features

- **Student Management**: Complete CRUD operations for student records
- **Family Information**: Track guardian and family details
- **Finance Management**: Track school fees payments and balances
- **Insurance Management**: Monitor health insurance coverage
- **Dashboard**: Visual statistics and charts using Chart.js
- **Reports**: Export data to PDF and Excel formats
- **Role-Based Access Control**: Admin, Program Officer, and Data Entry roles

## Technology Stack

- Django 5.0+
- PostgreSQL (or MySQL)
- Tailwind CSS (via django-tailwind)
- Chart.js for dashboards
- ReportLab & WeasyPrint for PDF exports
- OpenPyXL for Excel exports

## Installation

### Option A: Docker (Recommended)

The easiest way to run SIMS is using Docker:

```bash
# 1. Clone the repository
git clone <repository-url>
cd sims

# 2. Create environment file
cp env.example .env
# Edit .env and set your SECRET_KEY

# 3. Build and start
docker-compose up -d --build

# 4. Setup (migrations, groups, static files)
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_groups
docker-compose exec web python manage.py createsuperuser

# 5. Access the application
# Visit http://localhost:80
```

For more Docker details, see [DOCKER.md](DOCKER.md)

**Using Makefile (easier commands):**
```bash
make build      # Build images
make up         # Start services
make setup      # Run initial setup
make logs       # View logs
make shell      # Django shell
```

### Option B: Local Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd sims
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### PostgreSQL (Recommended)

Create a database:

```sql
CREATE DATABASE sims_db;
CREATE USER sims_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sims_db TO sims_user;
```

Update `sims/settings.py` with your database credentials.

#### MySQL (Alternative)

Update `sims/settings.py` to use MySQL configuration (commented section).

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Set up Tailwind CSS

```bash
python manage.py tailwind install
python manage.py tailwind build
```

### 7. Create superuser

```bash
python manage.py createsuperuser
```

### 8. Set up groups and permissions

```bash
python manage.py setup_groups
```

### 9. Run development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## User Roles and Permissions

The system includes three default groups:

1. **Admin**: Full access to all features
2. **Program Officer**: Can view/edit students, manage fees and insurance
3. **Data Entry**: Can add students, view records, and manage fees/insurance

Assign users to groups via Django admin or programmatically.

## Project Structure

```
sims/
├── accounts/          # Authentication and user management
├── core/             # Core models (School)
├── students/         # Student management
├── families/          # Family information
├── finance/          # School fees management
├── insurance/        # Health insurance management
├── dashboard/        # Dashboard views
├── reports/          # Report generation
├── templates/        # Django templates
├── static/           # Static files
└── media/            # Media uploads
```

## Usage

### Adding Students

1. Navigate to Students → Add Student
2. Fill in student information
3. Upload profile picture (optional)
4. Assign to a Program Officer

### Managing Fees

1. Go to Finance → Add Payment
2. Select student and term
3. Enter required fees and amount paid
4. Balance is calculated automatically

### Insurance Management

1. Navigate to Insurance → Add Insurance
2. Select student
3. Enter required amount and amount paid
4. Coverage status updates automatically

### Generating Reports

1. Go to Reports
2. Click on desired report type
3. PDF or Excel file will be downloaded

## Development

### Running Tests

```bash
python manage.py test
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Production Deployment

1. Set `DEBUG = False` in `settings.py`
2. Update `SECRET_KEY` with a secure key
3. Configure `ALLOWED_HOSTS`
4. Set up proper database credentials
5. Configure static file serving
6. Set up media file serving
7. Use a production WSGI server (e.g., Gunicorn)

## License

This project is developed for SolidAct Foundation.

## Support

For issues and questions, please contact the development team.

