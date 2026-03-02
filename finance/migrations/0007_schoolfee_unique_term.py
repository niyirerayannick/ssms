from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0006_alter_schoolfee_options'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='schoolfee',
            constraint=models.UniqueConstraint(
                fields=('student', 'academic_year', 'term'),
                name='unique_student_term_year_fee',
            ),
        ),
    ]
