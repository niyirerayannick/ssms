from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0016_studentenrollmenthistory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentmaterial',
            name='drawing_books_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='duplicating_papers_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='mathematical_sets_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='pens_pencils_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='periodic_tables_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='register_files_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='rulers_erasers_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='sanitary_pads_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentmaterial',
            name='scientific_calculators_received',
            field=models.BooleanField(default=False),
        ),
    ]
