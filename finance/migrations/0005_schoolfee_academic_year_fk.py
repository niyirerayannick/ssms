from django.db import migrations, models


def forwards_copy_academic_year(apps, schema_editor):
    SchoolFee = apps.get_model('finance', 'SchoolFee')
    AcademicYear = apps.get_model('core', 'AcademicYear')

    for fee in SchoolFee.objects.all().only('id', 'academic_year'):
        year_value = fee.academic_year
        if not year_value:
            continue
        year_obj, _ = AcademicYear.objects.get_or_create(name=str(year_value).strip())
        fee.academic_year_ref = year_obj
        fee.save(update_fields=['academic_year_ref'])


def backwards_copy_academic_year(apps, schema_editor):
    SchoolFee = apps.get_model('finance', 'SchoolFee')
    for fee in SchoolFee.objects.select_related('academic_year_ref').all().only('id', 'academic_year_ref'):
        if fee.academic_year_ref:
            fee.academic_year = fee.academic_year_ref.name
            fee.save(update_fields=['academic_year'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_academic_year'),
        ('finance', '0004_alter_schoolfee_term'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolfee',
            name='academic_year_ref',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='school_fees', to='core.academicyear'),
        ),
        migrations.RunPython(forwards_copy_academic_year, backwards_copy_academic_year),
        migrations.RemoveField(
            model_name='schoolfee',
            name='academic_year',
        ),
        migrations.RenameField(
            model_name='schoolfee',
            old_name='academic_year_ref',
            new_name='academic_year',
        ),
    ]
