from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_student_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='boarding_status',
            field=models.CharField(choices=[('boarding', 'Boarding'), ('non_boarding', 'Non-boarding')], default='non_boarding', max_length=20),
        ),
        migrations.AddField(
            model_name='student',
            name='school_level',
            field=models.CharField(choices=[('nursery', 'Nursery'), ('primary', 'Primary'), ('secondary', 'Secondary'), ('tvet', 'TVET')], default='primary', max_length=20),
        ),
    ]
