from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='daily_production_target',
            field=models.PositiveIntegerField(default=0, help_text='Target number of assemblies to complete per day. Set 0 to disable.'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='weekly_production_target',
            field=models.PositiveIntegerField(default=0, help_text='Target number of assemblies to complete per week. Set 0 to disable.'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='monthly_production_target',
            field=models.PositiveIntegerField(default=0, help_text='Target number of assemblies to complete per month. Set 0 to disable.'),
        ),
    ]
