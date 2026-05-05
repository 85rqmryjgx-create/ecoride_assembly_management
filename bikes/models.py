from django.db import models


class BikeModel(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'Bike Model'
        verbose_name_plural = 'Bike Models'

    def __str__(self):
        return f'{self.brand} {self.name} ({self.year})'


class Component(models.Model):
    CATEGORY_CHOICES = [
        ('frame', 'Frame'),
        ('motor', 'Motor'),
        ('battery', 'Battery'),
        ('brakes', 'Brakes'),
        ('transmission', 'Transmission'),
        ('wheels', 'Wheels'),
        ('electronics', 'Electronics'),
        ('other', 'Other'),
    ]

    bike_model = models.ForeignKey(BikeModel, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    part_number = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Component'
        verbose_name_plural = 'Components'

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'
