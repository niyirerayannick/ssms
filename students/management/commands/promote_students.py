from django.core.management.base import BaseCommand, CommandError

from core.academic_years import get_default_academic_year
from core.models import AcademicYear
from students.services.promotion import (
    get_or_create_next_academic_year,
    promote_students_to_academic_year,
)


class Command(BaseCommand):
    help = 'Copy enrolled students from one academic year into the next academic year.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-year',
            dest='from_year',
            help='Source academic year name, for example 2025-2026.',
        )
        parser.add_argument(
            '--to-year',
            dest='to_year',
            help='Target academic year name. If omitted, it is inferred from the source year.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Update target-year enrollment snapshots when they already exist.',
        )
        parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='Include inactive or non-enrolled students in the promotion run.',
        )
        parser.add_argument(
            '--activate-target',
            action='store_true',
            help='Mark the target academic year as active after promotion.',
        )

    def handle(self, *args, **options):
        source_year_name = options.get('from_year')
        target_year_name = options.get('to_year')

        if source_year_name:
            source_year = AcademicYear.objects.filter(name=source_year_name).first()
            if not source_year:
                raise CommandError(f'Academic year "{source_year_name}" was not found.')
        else:
            source_year = get_default_academic_year()
            if not source_year:
                raise CommandError('No academic year exists yet. Create one before running promotion.')

        if target_year_name:
            target_year, _ = AcademicYear.objects.get_or_create(
                name=target_year_name,
                defaults={'is_active': False},
            )
        else:
            try:
                target_year = get_or_create_next_academic_year(source_year.name)
            except ValueError as exc:
                raise CommandError(str(exc)) from exc

        if source_year.pk == target_year.pk:
            raise CommandError('Source and target academic years must be different.')

        summary = promote_students_to_academic_year(
            source_year,
            target_year,
            overwrite=options['overwrite'],
            include_inactive=options['include_inactive'],
            activate_target=options['activate_target'],
        )

        self.stdout.write(self.style.SUCCESS('Student promotion completed successfully.'))
        self.stdout.write(f'Source year: {summary.source_year.name}')
        self.stdout.write(f'Target year: {summary.target_year.name}')
        self.stdout.write(f'Created snapshots: {summary.created_count}')
        self.stdout.write(f'Updated snapshots: {summary.updated_count}')
        self.stdout.write(f'Skipped snapshots: {summary.skipped_count}')
        self.stdout.write(f'Graduated students: {summary.graduated_count}')
