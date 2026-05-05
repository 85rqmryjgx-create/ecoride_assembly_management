from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='Ecoride', max_length=100)),
                ('labor_rate_per_hour', models.DecimalField(
                    decimal_places=2, default=30.0, max_digits=6,
                    help_text='Labor cost per hour in € — used to calculate defect financial impact.'
                )),
                ('open_defect_alert_threshold', models.PositiveIntegerField(
                    default=5,
                    help_text='Show a dashboard warning when open defects exceed this number.'
                )),
            ],
            options={
                'verbose_name': 'App Settings',
                'verbose_name_plural': 'App Settings',
            },
        ),
    ]
