from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_schoolfee_unique_term'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolfee',
            name='payment_date',
            field=models.DateField(blank=True, help_text='Date the payment was recorded', null=True),
        ),
        migrations.AddField(
            model_name='schoolfee',
            name='recorded_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who recorded this payment',
                null=True,
                on_delete=models.SET_NULL,
                related_name='recorded_school_fees',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
