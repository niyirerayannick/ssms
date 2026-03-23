from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_fee_snapshots_and_payments(apps, schema_editor):
    SchoolFee = apps.get_model('finance', 'SchoolFee')
    SchoolFeePayment = apps.get_model('finance', 'SchoolFeePayment')

    for fee in SchoolFee.objects.select_related('student__school').all():
        student = fee.student
        school = student.school if student else None

        updates = []
        if not fee.school_name:
            fee.school_name = school.name if school else getattr(student, 'school_name', '')
            updates.append('school_name')
        if not fee.class_level and student:
            fee.class_level = student.class_level
            updates.append('class_level')
        if not fee.bank_name:
            fee.bank_name = school.bank_name if school and school.bank_name else ''
            updates.append('bank_name')
        if not fee.bank_account_name:
            fee.bank_account_name = school.bank_account_name if school and school.bank_account_name else ''
            updates.append('bank_account_name')
        if not fee.bank_account_number:
            fee.bank_account_number = school.bank_account_number if school and school.bank_account_number else ''
            updates.append('bank_account_number')
        if updates:
            fee.save(update_fields=updates)

        if fee.amount_paid and fee.amount_paid > 0 and not SchoolFeePayment.objects.filter(school_fee=fee).exists():
            SchoolFeePayment.objects.create(
                school_fee=fee,
                amount_paid=fee.amount_paid,
                payment_date=fee.payment_date or django.utils.timezone.now().date(),
                payment_method='bank',
                reference_number='',
                recorded_by=fee.recorded_by,
                notes=fee.comments or '',
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finance', '0010_schoolfee_enrollment_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolfee',
            name='bank_account_name',
            field=models.CharField(blank=True, help_text='Bank account holder snapshot', max_length=200),
        ),
        migrations.AddField(
            model_name='schoolfee',
            name='bank_account_number',
            field=models.CharField(blank=True, help_text='Bank account number snapshot', max_length=50),
        ),
        migrations.AddField(
            model_name='schoolfee',
            name='bank_name',
            field=models.CharField(blank=True, help_text='Bank name snapshot for this fee record', max_length=200),
        ),
        migrations.CreateModel(
            name='SchoolFeePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateField(default=django.utils.timezone.now)),
                ('payment_method', models.CharField(choices=[('bank', 'Bank Transfer'), ('cash', 'Cash'), ('mobile_money', 'Mobile Money'), ('other', 'Other')], default='bank', max_length=20)),
                ('reference_number', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_fee_payments_recorded', to=settings.AUTH_USER_MODEL)),
                ('school_fee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='finance.schoolfee')),
            ],
            options={
                'verbose_name': 'School Fee Payment',
                'verbose_name_plural': 'School Fee Payments',
                'ordering': ['-payment_date', '-created_at'],
            },
        ),
        migrations.RunPython(backfill_fee_snapshots_and_payments, migrations.RunPython.noop),
    ]
