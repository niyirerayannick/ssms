from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('families', '0005_family_total_family_members'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='father_name',
            field=models.CharField(blank=True, help_text="Father's full name", max_length=200),
        ),
        migrations.AddField(
            model_name='family',
            name='mother_name',
            field=models.CharField(blank=True, help_text="Mother's full name", max_length=200),
        ),
        migrations.AddField(
            model_name='family',
            name='is_orphan',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='family',
            name='guardian_name',
            field=models.CharField(blank=True, help_text='Guardian full name (if orphan)', max_length=200),
        ),
        migrations.AddField(
            model_name='family',
            name='guardian_phone',
            field=models.CharField(blank=True, help_text='Guardian phone number', max_length=20),
        ),
    ]
