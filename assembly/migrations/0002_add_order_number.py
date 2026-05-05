from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assembly', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assemblysession',
            name='order_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='Assembly Order Number'),
        ),
    ]
