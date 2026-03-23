from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0011_schoolfee_bank_snapshots_schoolfeepayment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schoolfee',
            name='enrollment_history',
        ),
    ]
