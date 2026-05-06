from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('defects', '0003_add_component'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefectComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Defect Component',
                'verbose_name_plural': 'Defect Components',
                'ordering': ['order', 'name'],
            },
        ),
    ]
