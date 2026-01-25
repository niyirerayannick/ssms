from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_student_sponsorship_start_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(help_text='e.g., 2024', max_length=20)),
                ('books_received', models.BooleanField(default=False)),
                ('bag_received', models.BooleanField(default=False)),
                ('shoes_received', models.BooleanField(default=False)),
                ('uniforms_received', models.BooleanField(default=False)),
                ('special_request', models.TextField(blank=True, help_text='Special needs or requests')),
                ('notes', models.TextField(blank=True)),
                ('received_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='material_records', to='students.student')),
            ],
            options={
                'ordering': ['-academic_year', 'student__first_name'],
                'unique_together': {('student', 'academic_year')},
            },
        ),
    ]
