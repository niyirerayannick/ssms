from django.db import migrations, models


def forwards_copy_academic_year(apps, schema_editor):
    StudentMark = apps.get_model('students', 'StudentMark')
    AcademicYear = apps.get_model('core', 'AcademicYear')

    for record in StudentMark.objects.all().only('id', 'academic_year'):
        year_value = record.academic_year
        if not year_value:
            continue
        year_obj, _ = AcademicYear.objects.get_or_create(name=str(year_value).strip())
        record.academic_year_ref = year_obj
        record.save(update_fields=['academic_year_ref'])


def backwards_copy_academic_year(apps, schema_editor):
    StudentMark = apps.get_model('students', 'StudentMark')
    for record in StudentMark.objects.select_related('academic_year_ref').all().only('id', 'academic_year_ref'):
        if record.academic_year_ref:
            record.academic_year = record.academic_year_ref.name
            record.save(update_fields=['academic_year'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_academic_year'),
        ('students', '0009_student_sponsorship_reason'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='studentmark',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='studentmark',
            name='academic_year_ref',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='student_marks', to='core.academicyear'),
        ),
        migrations.RunPython(forwards_copy_academic_year, backwards_copy_academic_year),
        migrations.RemoveField(
            model_name='studentmark',
            name='academic_year',
        ),
        migrations.RenameField(
            model_name='studentmark',
            old_name='academic_year_ref',
            new_name='academic_year',
        ),
        migrations.AlterUniqueTogether(
            name='studentmark',
            unique_together={('student', 'subject', 'term', 'academic_year')},
        ),
    ]
