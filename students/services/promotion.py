import re
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from core.models import AcademicYear
from students.models import StudentEnrollmentHistory, sync_student_enrollment_history


YEAR_NAME_PATTERN = re.compile(r'^\s*(\d{4})\s*[-/]\s*(\d{4})\s*$')
CLASS_LEVEL_PATTERN = re.compile(r'^\s*([A-Za-z]+)\s*[- ]?\s*(\d+)\s*$')
PRIMARY_PATTERN = re.compile(r'^\s*(PRIMARY|P)\s*(\d+)(.*)$', re.IGNORECASE)
SECONDARY_PATTERN = re.compile(r'^\s*(SENIOR|S)\s*(\d+)(.*)$', re.IGNORECASE)
NURSERY_PATTERN = re.compile(r'^\s*(NURSERY|N)\s*(\d+)(.*)$', re.IGNORECASE)
YEAR_PATTERN = re.compile(r'^\s*(YEAR|Y|LEVEL|L)\s*(\d+)(.*)$', re.IGNORECASE)


@dataclass
class PromotionSummary:
    source_year: AcademicYear
    target_year: AcademicYear
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    graduated_count: int = 0
    results: list = field(default_factory=list)


def infer_next_academic_year_name(year_name):
    """Convert a year label like 2025-2026 into 2026-2027."""

    match = YEAR_NAME_PATTERN.match((year_name or '').strip())
    if not match:
        return None

    start_year = int(match.group(1))
    end_year = int(match.group(2))
    return f'{start_year + 1}-{end_year + 1}'


def get_or_create_next_academic_year(source_year_name):
    """Return the next academic year, creating it when possible."""

    next_name = infer_next_academic_year_name(source_year_name)
    if not next_name:
        raise ValueError('Unable to infer the next academic year name from the source year.')

    target_year, _ = AcademicYear.objects.get_or_create(
        name=next_name,
        defaults={'is_active': False},
    )
    return target_year


def promote_class_level(class_level, school_level=''):
    """Return the next class level and school level for a yearly promotion."""

    value = (class_level or '').strip()
    school_level_value = (school_level or '').strip()
    if not value:
        return value, school_level_value, False

    normalized_words = ' '.join(value.upper().split())
    if normalized_words in {'BABY CLASS', 'BABY'}:
        return 'Middle Class', 'nursery', False
    if normalized_words in {'MIDDLE CLASS', 'MIDDLE'}:
        return 'Top Class', 'nursery', False
    if normalized_words in {'TOP CLASS', 'TOP'}:
        return 'Primary 1', 'primary', False

    primary_match = PRIMARY_PATTERN.match(value)
    if primary_match:
        number = int(primary_match.group(2))
        suffix = primary_match.group(3).rstrip()
        if number >= 6:
            next_value = 'Senior 1'
            return f'{next_value}{suffix}', 'secondary', False
        return f'Primary {number + 1}{suffix}', 'primary', False

    secondary_match = SECONDARY_PATTERN.match(value)
    if secondary_match:
        number = int(secondary_match.group(2))
        suffix = secondary_match.group(3).rstrip()
        if number >= 6:
            return value, school_level_value or 'secondary', True
        return f'Senior {number + 1}{suffix}', 'secondary', False

    nursery_match = NURSERY_PATTERN.match(value)
    if nursery_match:
        number = int(nursery_match.group(2))
        suffix = nursery_match.group(3).rstrip()
        if number >= 3:
            return f'Primary 1{suffix}', 'primary', False
        return f'Nursery {number + 1}{suffix}', 'nursery', False

    year_match = YEAR_PATTERN.match(value)
    if year_match:
        prefix = year_match.group(1).title()
        number = int(year_match.group(2))
        suffix = year_match.group(3).rstrip()
        return f'{prefix} {number + 1}{suffix}', school_level_value, False

    match = CLASS_LEVEL_PATTERN.match(value)
    if match:
        prefix = match.group(1).upper()
        number = int(match.group(2))
        return f'{prefix}{number + 1}', school_level_value, False

    return value, school_level_value, False


@transaction.atomic
def promote_students_to_academic_year(
    source_year,
    target_year,
    *,
    overwrite=False,
    include_inactive=False,
    activate_target=False,
):
    """Copy yearly enrollment snapshots into the target academic year."""

    histories = (
        StudentEnrollmentHistory.objects.select_related('student', 'school', 'academic_year')
        .filter(academic_year=source_year)
        .order_by('student__last_name', 'student__first_name')
    )
    if not include_inactive:
        histories = histories.filter(student__is_active=True, student__enrollment_status='enrolled')

    summary = PromotionSummary(source_year=source_year, target_year=target_year)
    promoted_on = timezone.now().date()

    for history in histories:
        student = history.student
        new_class_level, new_school_level, should_graduate = promote_class_level(
            history.class_level,
            history.school_level,
        )

        if should_graduate:
            student_updates = []
            if student.enrollment_status != 'graduated':
                student.enrollment_status = 'graduated'
                student_updates.append('enrollment_status')
            if getattr(student, 'sponsorship_status', None) != 'graduated':
                student.sponsorship_status = 'graduated'
                student_updates.append('sponsorship_status')
            if student.is_active:
                student.is_active = False
                student_updates.append('is_active')
            if student_updates:
                student_updates.append('updated_at')
                student.save(update_fields=student_updates)
            summary.graduated_count += 1
            summary.skipped_count += 1
            summary.results.append({
                'student_id': student.pk,
                'student_name': student.full_name,
                'from_class': history.class_level or '-',
                'to_class': '-',
                'from_level': history.school_level or '-',
                'to_level': '-',
                'status': 'graduated',
                'message': 'Student reached the terminal class and was marked graduated.',
            })
            continue

        overrides = {
            'class_level': new_class_level,
            'school': history.school,
            'school_name': history.display_school_name,
            'school_level': new_school_level,
        }

        existing_target = StudentEnrollmentHistory.objects.filter(
            student=student,
            academic_year=target_year,
        ).first()
        if existing_target and not overwrite:
            summary.skipped_count += 1
            summary.results.append({
                'student_id': student.pk,
                'student_name': student.full_name,
                'from_class': history.class_level or '-',
                'to_class': existing_target.class_level or new_class_level or '-',
                'from_level': history.school_level or '-',
                'to_level': existing_target.school_level or new_school_level or '-',
                'status': 'skipped',
                'message': 'Target academic year already has a snapshot and overwrite was disabled.',
            })
            continue

        snapshot = sync_student_enrollment_history(
            student,
            target_year,
            overrides=overrides,
            overwrite=True,
            promoted_on=promoted_on,
        )

        if existing_target:
            summary.updated_count += 1
            result_status = 'updated'
            result_message = 'Existing target-year snapshot was refreshed.'
        elif snapshot:
            summary.created_count += 1
            result_status = 'created'
            result_message = 'New target-year snapshot was created.'
        else:
            result_status = 'skipped'
            result_message = 'No target-year snapshot was created.'

        student_updates = []
        if student.class_level != new_class_level:
            student.class_level = new_class_level
            student_updates.append('class_level')
        if student.school_id != history.school_id:
            student.school = history.school
            student_updates.append('school')
        if student.school_name != history.display_school_name:
            student.school_name = history.display_school_name
            student_updates.append('school_name')
        if student.school_level != new_school_level:
            student.school_level = new_school_level
            student_updates.append('school_level')

        if student_updates:
            student_updates.append('updated_at')
            student.save(update_fields=student_updates)

        summary.results.append({
            'student_id': student.pk,
            'student_name': student.full_name,
            'from_class': history.class_level or '-',
            'to_class': new_class_level or '-',
            'from_level': history.school_level or '-',
            'to_level': new_school_level or '-',
            'status': result_status,
            'message': result_message,
        })

    if activate_target and not target_year.is_active:
        target_year.is_active = True
        target_year.save(update_fields=['is_active'])

    return summary
