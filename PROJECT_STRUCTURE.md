# SIMS Project Structure

```
sims/
├── accounts/                    # Authentication app
│   ├── management/
│   │   └── commands/
│   │       └── setup_groups.py  # Command to setup user groups
│   ├── models.py
│   ├── views.py                 # Login/logout views
│   └── urls.py
│
├── core/                        # Core models
│   ├── models.py                # School model
│   └── admin.py
│
├── students/                    # Student management
│   ├── models.py               # Student model
│   ├── views.py                # CRUD views
│   ├── forms.py                # StudentForm
│   ├── urls.py
│   └── admin.py
│
├── families/                    # Family information
│   ├── models.py               # Family model
│   ├── views.py                # Family CRUD
│   ├── forms.py                # FamilyForm
│   ├── urls.py
│   └── admin.py
│
├── finance/                     # School fees
│   ├── models.py               # SchoolFees model
│   ├── views.py                # Fees management
│   ├── forms.py                # FeeForm
│   ├── urls.py
│   └── admin.py
│
├── insurance/                   # Health insurance
│   ├── models.py               # HealthInsurance model
│   ├── views.py                # Insurance management
│   ├── forms.py                # InsuranceForm
│   ├── urls.py
│   └── admin.py
│
├── dashboard/                   # Dashboard
│   ├── views.py                # Dashboard with statistics
│   └── urls.py
│
├── reports/                     # Report generation
│   ├── views.py                # PDF & Excel exports
│   └── urls.py
│
├── theme/                       # Tailwind CSS theme
│   ├── static_src/
│   │   ├── src/
│   │   │   └── styles.css
│   │   ├── package.json
│   │   └── tailwind.config.js
│   └── apps.py
│
├── templates/                   # Django templates
│   ├── base.html               # Base template
│   ├── partials/
│   │   ├── navbar.html
│   │   └── sidebar.html
│   ├── accounts/
│   │   └── login.html
│   ├── dashboard/
│   │   └── index.html          # Dashboard with Chart.js
│   ├── students/
│   │   ├── student_list.html
│   │   ├── student_form.html
│   │   └── student_detail.html
│   ├── families/
│   │   └── family_form.html
│   ├── finance/
│   │   ├── fees_list.html
│   │   ├── fee_form.html
│   │   └── overdue_fees.html
│   ├── insurance/
│   │   ├── insurance_list.html
│   │   ├── insurance_form.html
│   │   └── coverage_summary.html
│   └── reports/
│       └── index.html
│
├── static/                      # Static files
├── media/                       # Media uploads
│
├── sims/                        # Project settings
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── manage.py
├── requirements.txt
├── README.md
├── QUICKSTART.md
└── setup.py                     # Setup script
```

## Key Features Implemented

✅ **Models**: Student, Family, School, SchoolFees, HealthInsurance
✅ **Views**: Complete CRUD for all modules
✅ **Forms**: Django forms with Tailwind styling
✅ **Templates**: All pages with responsive Tailwind design
✅ **Authentication**: Django built-in auth with groups
✅ **Permissions**: Role-based access control
✅ **Dashboard**: Statistics and Chart.js visualizations
✅ **Reports**: PDF (ReportLab) and Excel (OpenPyXL) exports
✅ **Tailwind CSS**: Fully integrated via django-tailwind

## Database Schema

- **Student** → OneToOne → **Family**
- **Student** → ForeignKey → **School**
- **Student** → ForeignKey → **User** (program_officer)
- **SchoolFees** → ForeignKey → **Student**
- **HealthInsurance** → ForeignKey → **Student**

## Permissions

- `students.add_student`
- `students.change_student`
- `students.view_student`
- `finance.manage_fees`
- `insurance.manage_insurance`

## User Groups

1. **Admin**: All permissions
2. **Program Officer**: View/edit students, manage fees & insurance
3. **Data Entry**: Add students, view, manage fees & insurance

