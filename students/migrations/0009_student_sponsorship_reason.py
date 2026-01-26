from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_student_boarding_school_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='sponsorship_reason',
            field=models.TextField(blank=True, help_text='Reason Solidact is supporting this student'),
        ),
    ]
