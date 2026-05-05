from django.db import models
from django.conf import settings
from assembly.models import AssemblySession, StepExecution


class Defect(models.Model):
    TYPE_MANUFACTURING = 'manufacturing'
    TYPE_ASSEMBLY = 'assembly'
    TYPE_OTHER = 'other'

    TYPE_CHOICES = [
        (TYPE_MANUFACTURING, 'Manufacturing Defect'),
        (TYPE_ASSEMBLY, 'Assembly Issue'),
        (TYPE_OTHER, 'Other'),
    ]

    COMPONENT_FRAME = 'frame'
    COMPONENT_MOTOR = 'motor'
    COMPONENT_BATTERY = 'battery'
    COMPONENT_BRAKES = 'brakes'
    COMPONENT_TRANSMISSION = 'transmission'
    COMPONENT_WHEELS = 'wheels'
    COMPONENT_ELECTRONICS = 'electronics'
    COMPONENT_OTHER = 'other'

    COMPONENT_CHOICES = [
        (COMPONENT_FRAME, 'Frame'),
        (COMPONENT_MOTOR, 'Motor'),
        (COMPONENT_BATTERY, 'Battery'),
        (COMPONENT_BRAKES, 'Brakes'),
        (COMPONENT_TRANSMISSION, 'Transmission'),
        (COMPONENT_WHEELS, 'Wheels'),
        (COMPONENT_ELECTRONICS, 'Electronics'),
        (COMPONENT_OTHER, 'Other'),
    ]

    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    component = models.CharField(max_length=30, choices=COMPONENT_CHOICES, blank=True, verbose_name='Affected Component')

    session = models.ForeignKey(AssemblySession, on_delete=models.CASCADE, related_name='defects')
    step_execution = models.ForeignKey(
        StepExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='defects'
    )
    defect_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    step_note = models.CharField(max_length=255, blank=True, verbose_name='Related Step / Note')
    description = models.TextField()
    photo = models.ImageField(upload_to='defects/%Y/%m/', blank=True, null=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_defects'
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    resolution_description = models.TextField(blank=True)
    resolution_minutes = models.PositiveIntegerField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_defects'
    )

    class Meta:
        ordering = ['-reported_at']
        verbose_name = 'Defect'
        verbose_name_plural = 'Defects'

    def __str__(self):
        return f'{self.get_defect_type_display()} — {self.session} ({self.get_severity_display()})'

    @property
    def is_resolved(self):
        return self.resolved_at is not None
