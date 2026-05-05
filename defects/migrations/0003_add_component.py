from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('defects', '0002_add_step_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='defect',
            name='component',
            field=models.CharField(
                blank=True,
                choices=[
                    ('frame', 'Frame'),
                    ('motor', 'Motor'),
                    ('battery', 'Battery'),
                    ('brakes', 'Brakes'),
                    ('transmission', 'Transmission'),
                    ('wheels', 'Wheels'),
                    ('electronics', 'Electronics'),
                    ('other', 'Other'),
                ],
                max_length=30,
                verbose_name='Affected Component',
            ),
        ),
    ]
