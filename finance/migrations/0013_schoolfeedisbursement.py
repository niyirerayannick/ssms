from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finance', '0012_remove_schoolfee_enrollment_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolFeeDisbursement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(blank=True, max_length=200)),
                ('school_name', models.CharField(blank=True, max_length=200)),
                ('class_level', models.CharField(blank=True, max_length=50)),
                ('bank_name', models.CharField(blank=True, max_length=200)),
                ('bank_account_name', models.CharField(blank=True, max_length=200)),
                ('bank_account_number', models.CharField(blank=True, max_length=50)),
                ('amount_to_pay', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('exported', 'Exported'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('exported_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('payment_reference', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paid_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_school_fee_disbursements', to=settings.AUTH_USER_MODEL)),
                ('school_fee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='disbursement', to='finance.schoolfee')),
            ],
            options={
                'verbose_name': 'School Fee Disbursement',
                'verbose_name_plural': 'School Fee Disbursements',
                'ordering': ['-requested_at'],
            },
        ),
    ]
