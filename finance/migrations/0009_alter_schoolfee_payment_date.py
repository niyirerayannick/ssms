import django.utils.timezone
from django.db import migrations, models


def set_missing_payment_dates(apps, schema_editor):
    SchoolFee = apps.get_model('finance', 'SchoolFee')
    for fee in SchoolFee.objects.filter(payment_date__isnull=True):
        fee.payment_date = fee.created_at.date() if fee.created_at else django.utils.timezone.now().date()
        fee.save(update_fields=['payment_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0008_schoolfee_recorded_by_payment_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolfee',
            name='payment_date',
            field=models.DateField(
                blank=True,
                default=django.utils.timezone.now,
                help_text='Date the payment was recorded',
                null=True,
            ),
        ),
        migrations.RunPython(set_missing_payment_dates, migrations.RunPython.noop),
    ]
