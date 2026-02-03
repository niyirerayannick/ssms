"""
Management command to set up user groups and permissions.
Run: python manage.py setup_groups
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from students.models import Student
from finance.models import SchoolFee
from insurance.models import HealthInsurance


class Command(BaseCommand):
    help = 'Set up user groups and assign permissions'

    def handle(self, *args, **options):
        # Create groups
        admin_group, created = Group.objects.get_or_create(name='Admin')
        program_officer_group, created = Group.objects.get_or_create(name='Program Officer')
        data_entry_group, created = Group.objects.get_or_create(name='Data Entry')

        # Get content types
        student_ct = ContentType.objects.get_for_model(Student)
        fees_ct = ContentType.objects.get_for_model(SchoolFee)
        insurance_ct = ContentType.objects.get_for_model(HealthInsurance)

        # Get permissions
        add_student = Permission.objects.get(codename='add_student', content_type=student_ct)
        change_student = Permission.objects.get(codename='change_student', content_type=student_ct)
        view_student = Permission.objects.get(codename='view_student', content_type=student_ct)
        
        # Ensure custom permissions exist (migration may not have created them yet)
        manage_fees, _ = Permission.objects.get_or_create(
            codename='manage_fees',
            content_type=fees_ct,
            defaults={'name': 'Can manage fees'},
        )
        manage_insurance, _ = Permission.objects.get_or_create(
            codename='manage_insurance',
            content_type=insurance_ct,
            defaults={'name': 'Can manage insurance'},
        )

        # Admin group - all permissions
        admin_group.permissions.add(
            add_student, change_student, view_student,
            manage_fees, manage_insurance
        )

        # Program Officer group - view and manage students, fees, insurance
        program_officer_group.permissions.add(
            view_student, change_student,
            manage_fees, manage_insurance
        )

        # Data Entry group - add and view only
        data_entry_group.permissions.add(
            add_student, view_student,
            manage_fees, manage_insurance
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully set up groups and permissions:\n'
                '- Admin: Full access\n'
                '- Program Officer: View/Edit students, manage fees & insurance\n'
                '- Data Entry: Add students, view, manage fees & insurance'
            )
        )

