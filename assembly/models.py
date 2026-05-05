from django.db import models
from django.conf import settings
from bikes.models import BikeModel


class AssemblyProcess(models.Model):
    bike_model = models.ForeignKey(BikeModel, on_delete=models.CASCADE, related_name='processes')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assembly Process'
        verbose_name_plural = 'Assembly Processes'

    def __str__(self):
        return f'{self.bike_model} — {self.name}'

    def total_estimated_minutes(self):
        return sum(s.estimated_minutes for s in self.steps.all())


class AssemblyStep(models.Model):
    process = models.ForeignKey(AssemblyProcess, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Assembly Step'
        verbose_name_plural = 'Assembly Steps'

    def __str__(self):
        return f'{self.order}. {self.name}'


class AssemblySession(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_PAUSED = 'paused'

    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_PAUSED, 'Paused'),
    ]

    bike_model = models.ForeignKey(BikeModel, on_delete=models.PROTECT)
    process = models.ForeignKey(AssemblyProcess, on_delete=models.PROTECT)
    order_number = models.CharField(max_length=50, blank=True, verbose_name='Assembly Order Number')
    serial_number = models.CharField(max_length=100, blank=True)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sessions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Assembly Session'
        verbose_name_plural = 'Assembly Sessions'

    def __str__(self):
        order = f' · {self.order_number}' if self.order_number else ''
        return f'{self.bike_model} — #{self.pk}{order} ({self.get_status_display()})'

    def total_actual_minutes(self):
        return sum(e.actual_minutes or 0 for e in self.step_executions.all())

    def total_estimated_minutes(self):
        return self.process.total_estimated_minutes()


class StepExecution(models.Model):
    session = models.ForeignKey(AssemblySession, on_delete=models.CASCADE, related_name='step_executions')
    step = models.ForeignKey(AssemblyStep, on_delete=models.PROTECT)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    actual_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['step__order']
        verbose_name = 'Step Execution'
        verbose_name_plural = 'Step Executions'

    def __str__(self):
        return f'{self.session} → {self.step}'
