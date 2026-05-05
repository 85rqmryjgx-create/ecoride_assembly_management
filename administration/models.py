from django.db import models


class AppSettings(models.Model):
    company_name = models.CharField(max_length=100, default='Ecoride')
    labor_rate_per_hour = models.DecimalField(
        max_digits=6, decimal_places=2, default=30.00,
        help_text='Labor cost per hour in € — used to calculate defect financial impact.'
    )
    open_defect_alert_threshold = models.PositiveIntegerField(
        default=5,
        help_text='Show a dashboard warning when open defects exceed this number.'
    )

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return 'App Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
