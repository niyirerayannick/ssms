from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import AcademicYear, School, Partner
from families.models import Family, FamilyStudent
from students.models import Student, sync_student_enrollment_history


PROMOTION_DEMO_STUDENTS = [
    ('Baby', 'Class', 'nursery', 'Baby Class'),
    ('Middle', 'Class', 'nursery', 'Middle Class'),
    ('Top', 'Class', 'nursery', 'Top Class'),
    ('Primary', 'One', 'primary', 'Primary 1'),
    ('Primary', 'Six', 'primary', 'Primary 6'),
    ('Secondary', 'One', 'secondary', 'Senior 1'),
    ('Secondary', 'Five', 'secondary', 'Senior 5 STEM'),
    ('Secondary', 'Six', 'secondary', 'Senior 6 MCB'),
    ('TVET', 'One', 'tvet', 'Level 1'),
    ('University', 'Two', 'university', 'Year 2'),
]


class Command(BaseCommand):
    help = 'Seed local demo students across all school categories for promotion testing.'

    def add_arguments(self, parser):
        parser.add_argument('--source-year', default='2030-2031')
        parser.add_argument('--activate-source', action='store_true')

    def handle(self, *args, **options):
        source_year_name = options['source_year']
        source_year, _ = AcademicYear.objects.get_or_create(
            name=source_year_name,
            defaults={'is_active': options['activate_source']},
        )
        if options['activate_source'] and not source_year.is_active:
            source_year.is_active = True
            source_year.save(update_fields=['is_active'])

        partner, _ = Partner.objects.get_or_create(
            name='Promotion Demo Partner',
            defaults={'description': 'Seeded partner for promotion workflow testing.'},
        )

        created_count = 0
        with transaction.atomic():
            for index, (first_name, last_name, school_level, class_level) in enumerate(PROMOTION_DEMO_STUDENTS, start=1):
                family, _ = Family.objects.get_or_create(
                    national_id=f'990000000000{index:04d}',
                    defaults={
                        'head_of_family': f'{first_name} Household',
                        'phone_number': f'+25078000{index:04d}',
                        'total_family_members': 4,
                    },
                )
                school, _ = School.objects.get_or_create(
                    name=f'{school_level.title()} Demo School',
                    defaults={
                        'fee_amount': 12000,
                    },
                )

                student, created = Student.objects.update_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date(2010, 1, min(index, 28)),
                    defaults={
                        'family': family,
                        'gender': 'F' if index % 2 else 'M',
                        'school': school,
                        'school_name': school.name,
                        'class_level': class_level,
                        'school_level': school_level,
                        'enrollment_status': 'enrolled',
                        'boarding_status': 'non_boarding',
                        'sponsorship_status': 'active',
                        'partner': partner,
                        'is_active': True,
                    },
                )
                if created:
                    created_count += 1

                FamilyStudent.objects.update_or_create(
                    student=student,
                    defaults={
                        'family': family,
                        'relationship': 'Child',
                    },
                )
                sync_student_enrollment_history(student, source_year, overwrite=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'Promotion demo data ready in {source_year.name}. Seeded {len(PROMOTION_DEMO_STUDENTS)} students; {created_count} newly created.'
            )
        )
