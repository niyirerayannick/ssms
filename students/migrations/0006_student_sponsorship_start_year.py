from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_sponsorship_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='sponsorship_start_year',
            field=models.IntegerField(blank=True, help_text='Year sponsorship started (e.g., 2022)', null=True),
        ),
    ]
