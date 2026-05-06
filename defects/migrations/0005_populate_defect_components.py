from django.db import migrations

DEFAULT_COMPONENTS = [
    ('frame', 'Frame', 1),
    ('motor', 'Motor', 2),
    ('battery', 'Battery', 3),
    ('brakes', 'Brakes', 4),
    ('transmission', 'Transmission', 5),
    ('wheels', 'Wheels', 6),
    ('electronics', 'Electronics', 7),
    ('other', 'Other', 8),
]


def populate_components(apps, schema_editor):
    DefectComponent = apps.get_model('defects', 'DefectComponent')
    for code, name, order in DEFAULT_COMPONENTS:
        DefectComponent.objects.get_or_create(code=code, defaults={'name': name, 'order': order})


class Migration(migrations.Migration):

    dependencies = [
        ('defects', '0004_add_defect_component'),
    ]

    operations = [
        migrations.RunPython(populate_components, migrations.RunPython.noop),
    ]
