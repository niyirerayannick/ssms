from django.db import migrations, models
import django.db.models.deletion


def _normalize_account_number(value):
    return ''.join(str(value or '').split())


def backfill_school_fee_history(apps, schema_editor):
    SchoolFee = apps.get_model('finance', 'SchoolFee')
    AcademicYear = apps.get_model('core', 'AcademicYear')
    StudentEnrollmentHistory = apps.get_model('students', 'StudentEnrollmentHistory')

    fallback_year = AcademicYear.objects.order_by('-is_active', '-name').first()

    for fee in SchoolFee.objects.select_related('student', 'academic_year').all():
        student = fee.student
        changed_fields = []

        if fee.academic_year_id is None and fallback_year is not None:
            fee.academic_year_id = fallback_year.id
            changed_fields.append('academic_year')

        if not student or not fee.academic_year_id:
            if changed_fields:
                fee.save(update_fields=changed_fields)
            continue

        history, _created = StudentEnrollmentHistory.objects.get_or_create(
            student_id=student.id,
            academic_year_id=fee.academic_year_id,
            defaults={
                'class_level': getattr(student, 'class_level', '') or '',
                'school_id': getattr(student, 'school_id', None),
                'school_name': (
                    getattr(student.school, 'name', '') if getattr(student, 'school_id', None) else getattr(student, 'school_name', '')
                ) or '',
                'school_level': getattr(student, 'school_level', '') or '',
            },
        )

        history_fields = []
        if not history.class_level and getattr(student, 'class_level', ''):
            history.class_level = student.class_level
            history_fields.append('class_level')
        if not history.school_id and getattr(student, 'school_id', None):
            history.school_id = student.school_id
            history_fields.append('school')
        if not history.school_name:
            history.school_name = (
                getattr(student.school, 'name', '') if getattr(student, 'school_id', None) else getattr(student, 'school_name', '')
            ) or ''
            history_fields.append('school_name')
        if not history.school_level and getattr(student, 'school_level', ''):
            history.school_level = student.school_level
            history_fields.append('school_level')
        if history_fields:
            history.save(update_fields=history_fields)

        if fee.enrollment_history_id != history.id:
            fee.enrollment_history_id = history.id
            changed_fields.append('enrollment_history')
        if fee.school_id != history.school_id:
            fee.school_id = history.school_id
            changed_fields.append('school')
        if not fee.school_name:
            fee.school_name = history.school_name or (history.school.name if history.school_id else '')
            changed_fields.append('school_name')
        if not fee.class_level:
            fee.class_level = history.class_level or ''
            changed_fields.append('class_level')
        if not getattr(fee, 'school_level', ''):
            fee.school_level = history.school_level or ''
            changed_fields.append('school_level')
        if history.school_id:
            school = history.school
            if not fee.bank_name:
                fee.bank_name = school.bank_name or ''
                changed_fields.append('bank_name')
            if not fee.bank_account_name:
                fee.bank_account_name = school.bank_account_name or ''
                changed_fields.append('bank_account_name')
            if not fee.bank_account_number:
                fee.bank_account_number = _normalize_account_number(school.bank_account_number)
                changed_fields.append('bank_account_number')

        if changed_fields:
            fee.save(update_fields=list(dict.fromkeys(changed_fields)))


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0017_studentmaterial_material_package_expansion'),
        ('finance', '0013_schoolfeedisbursement'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolfee',
            name='enrollment_history',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_fees', to='students.studentenrollmenthistory'),
        ),
        migrations.AddField(
            model_name='schoolfee',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_fees', to='core.school'),
        ),
        migrations.AddField(
            model_name='schoolfee',
            name='school_level',
            field=models.CharField(blank=True, choices=[('nursery', 'Nursery'), ('primary', 'Primary'), ('secondary', 'Secondary'), ('tvet', 'TVET'), ('university', 'University')], max_length=20),
        ),
        migrations.AddField(
            model_name='schoolfeepayment',
            name='idempotency_key',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
        migrations.RunPython(backfill_school_fee_history, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='schoolfee',
            name='academic_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='school_fees', to='core.academicyear'),
        ),
        migrations.AddConstraint(
            model_name='schoolfee',
            constraint=models.CheckConstraint(check=models.Q(('total_fees__gte', 0)), name='school_fee_total_fees_gte_zero'),
        ),
        migrations.AddConstraint(
            model_name='schoolfee',
            constraint=models.CheckConstraint(check=models.Q(('amount_paid__gte', 0)), name='school_fee_amount_paid_gte_zero'),
        ),
        migrations.AddConstraint(
            model_name='schoolfee',
            constraint=models.CheckConstraint(check=models.Q(('balance__gte', 0)), name='school_fee_balance_gte_zero'),
        ),
        migrations.AddConstraint(
            model_name='schoolfeepayment',
            constraint=models.CheckConstraint(check=models.Q(('amount_paid__gt', 0)), name='school_fee_payment_amount_gt_zero'),
        ),
    ]
