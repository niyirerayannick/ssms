from django.db import migrations, models


def forwards_copy_insurance_year(apps, schema_editor):
    FamilyInsurance = apps.get_model('insurance', 'FamilyInsurance')
    AcademicYear = apps.get_model('core', 'AcademicYear')

    for record in FamilyInsurance.objects.all().only('id', 'insurance_year'):
        year_value = record.insurance_year
        if not year_value:
            continue
        year_obj, _ = AcademicYear.objects.get_or_create(name=str(year_value).strip())
        record.insurance_year_ref = year_obj
        record.save(update_fields=['insurance_year_ref'])


def backwards_copy_insurance_year(apps, schema_editor):
    FamilyInsurance = apps.get_model('insurance', 'FamilyInsurance')
    for record in FamilyInsurance.objects.select_related('insurance_year_ref').all().only('id', 'insurance_year_ref'):
        if record.insurance_year_ref:
            record.insurance_year = record.insurance_year_ref.name
            record.save(update_fields=['insurance_year'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_academic_year'),
        ('insurance', '0003_remove_familyinsurance_notes_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='familyinsurance',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='familyinsurance',
            name='insurance_year_ref',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='insurance_records', to='core.academicyear'),
        ),
        migrations.RunPython(forwards_copy_insurance_year, backwards_copy_insurance_year),
        migrations.RemoveField(
            model_name='familyinsurance',
            name='insurance_year',
        ),
        migrations.RenameField(
            model_name='familyinsurance',
            old_name='insurance_year_ref',
            new_name='insurance_year',
        ),
        migrations.AlterUniqueTogether(
            name='familyinsurance',
            unique_together={('family', 'insurance_year')},
        ),
    ]
