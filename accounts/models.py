from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_WORKER = 'worker'
    ROLE_TEAM_LEAD = 'team_lead'
    ROLE_SUPERVISOR = 'supervisor'

    ROLE_CHOICES = [
        (ROLE_WORKER, 'Worker'),
        (ROLE_TEAM_LEAD, 'Team Lead'),
        (ROLE_SUPERVISOR, 'Supervisor'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_WORKER)

    @property
    def is_worker(self):
        return self.role == self.ROLE_WORKER

    @property
    def is_team_lead(self):
        return self.role == self.ROLE_TEAM_LEAD

    @property
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR

    salary_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Monthly Salary (Kr)')
    must_change_password = models.BooleanField(default=False)

    @property
    def is_lead_or_above(self):
        return self.role in [self.ROLE_TEAM_LEAD, self.ROLE_SUPERVISOR]

    @property
    def hourly_rate(self):
        if self.salary_monthly:
            return round(float(self.salary_monthly) / 173, 2)
        return None

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'
