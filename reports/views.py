import datetime
import calendar
import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum, Count, Q

from assembly.models import AssemblySession, StepExecution
from defects.models import Defect
from bikes.models import BikeModel
from administration.models import AppSettings


class SupervisorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_supervisor:
            messages.error(request, 'Access restricted to Supervisors.')
            return redirect('assembly:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ReportIndexView(SupervisorRequiredMixin, TemplateView):
    template_name = 'reports/index.html'


def _get_report_data(start_date, end_date):
    app_settings = AppSettings.get()
    labor_rate = float(app_settings.labor_rate_per_hour)

    sessions = AssemblySession.objects.filter(
        status=AssemblySession.STATUS_COMPLETED,
        finished_at__date__gte=start_date,
        finished_at__date__lte=end_date,
    ).select_related('bike_model', 'process', 'worker')

    defects = Defect.objects.filter(
        reported_at__date__gte=start_date,
        reported_at__date__lte=end_date,
    ).select_related('session__bike_model', 'reported_by')

    # Fix N+1: use aggregate instead of per-session iteration
    total_assembly_minutes = StepExecution.objects.filter(
        session__in=sessions
    ).aggregate(total=Sum('actual_minutes'))['total'] or 0

    resolved_defects = defects.filter(resolved_at__isnull=False)
    total_resolution_minutes = resolved_defects.aggregate(
        total=Sum('resolution_minutes')
    )['total'] or 0

    # Financial calculations
    assembly_labor_cost = round((total_assembly_minutes / 60) * labor_rate, 2)
    defect_repair_cost = round((total_resolution_minutes / 60) * labor_rate, 2)
    total_sessions = sessions.count()
    cost_per_unit = round((assembly_labor_cost + defect_repair_cost) / total_sessions, 2) if total_sessions else 0
    defect_rate = round(defects.count() / total_sessions, 2) if total_sessions else 0

    defects_by_type = {
        'manufacturing': defects.filter(defect_type='manufacturing').count(),
        'assembly': defects.filter(defect_type='assembly').count(),
        'other': defects.filter(defect_type='other').count(),
    }

    defects_by_severity = {
        'critical': defects.filter(severity='critical').count(),
        'high': defects.filter(severity='high').count(),
        'medium': defects.filter(severity='medium').count(),
        'low': defects.filter(severity='low').count(),
    }

    # Component breakdown with financial cost
    component_costs = []
    for code, label in Defect.COMPONENT_CHOICES:
        group = defects.filter(component=code)
        count = group.count()
        if count:
            minutes = group.filter(resolved_at__isnull=False).aggregate(
                total=Sum('resolution_minutes')
            )['total'] or 0
            cost = round((minutes / 60) * labor_rate, 2)
            component_costs.append({'component': label, 'count': count, 'cost': cost})
    component_costs.sort(key=lambda x: x['cost'], reverse=True)

    bikes_summary = []
    for bike in BikeModel.objects.filter(active=True):
        bike_sessions = sessions.filter(bike_model=bike)
        bike_defects = defects.filter(session__bike_model=bike)
        if bike_sessions.exists() or bike_defects.exists():
            bike_minutes = StepExecution.objects.filter(
                session__in=bike_sessions
            ).aggregate(total=Sum('actual_minutes'))['total'] or 0
            count = bike_sessions.count()
            bikes_summary.append({
                'bike': bike,
                'sessions': count,
                'avg_minutes': round(bike_minutes / count, 1) if count else 0,
                'defects': bike_defects.count(),
            })

    return {
        'sessions': sessions,
        'defects': defects,
        'total_sessions': total_sessions,
        'total_assembly_minutes': total_assembly_minutes,
        'total_defects': defects.count(),
        'open_defects': defects.filter(resolved_at__isnull=True).count(),
        'total_resolution_minutes': total_resolution_minutes,
        'defects_by_type': defects_by_type,
        'defects_by_severity': defects_by_severity,
        'bikes_summary': bikes_summary,
        # Financial
        'labor_rate': labor_rate,
        'assembly_labor_cost': assembly_labor_cost,
        'defect_repair_cost': defect_repair_cost,
        'cost_per_unit': cost_per_unit,
        'defect_rate': defect_rate,
        'component_costs': component_costs,
    }


class ReportExportCSVView(SupervisorRequiredMixin, View):
    def get(self, request):
        period = request.GET.get('period', 'monthly')
        today = timezone.now().date()

        if period == 'weekly':
            week_offset = int(request.GET.get('week', 0))
            start_date = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(weeks=week_offset)
            end_date = start_date + datetime.timedelta(days=6)
            filename = f'report_week_{start_date.strftime("%Y-%m-%d")}.csv'
        else:
            month = int(request.GET.get('month', today.month))
            year = int(request.GET.get('year', today.year))
            last_day = calendar.monthrange(year, month)[1]
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, last_day)
            filename = f'report_{start_date.strftime("%Y-%m")}.csv'

        data = _get_report_data(start_date, end_date)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        writer.writerow(['ECORIDE ASSEMBLY REPORT'])
        writer.writerow([f'Period: {start_date} to {end_date}'])
        writer.writerow([f'Labor Rate: €{data["labor_rate"]}/h'])
        writer.writerow([])

        writer.writerow(['SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Assemblies Completed', data['total_sessions']])
        writer.writerow(['Total Assembly Minutes', data['total_assembly_minutes']])
        writer.writerow(['Total Defects', data['total_defects']])
        writer.writerow(['Open Defects', data['open_defects']])
        writer.writerow(['Repair Minutes', data['total_resolution_minutes']])
        writer.writerow(['Assembly Labor Cost (€)', data['assembly_labor_cost']])
        writer.writerow(['Defect Repair Cost (€)', data['defect_repair_cost']])
        writer.writerow(['Cost per Unit (€)', data['cost_per_unit']])
        writer.writerow(['Defect Rate (defects/unit)', data['defect_rate']])
        writer.writerow([])

        writer.writerow(['DEFECTS BY TYPE'])
        writer.writerow(['Type', 'Count'])
        writer.writerow(['Manufacturing', data['defects_by_type']['manufacturing']])
        writer.writerow(['Assembly', data['defects_by_type']['assembly']])
        writer.writerow(['Other', data['defects_by_type']['other']])
        writer.writerow([])

        writer.writerow(['DEFECTS BY SEVERITY'])
        writer.writerow(['Severity', 'Count'])
        for sev in ['critical', 'high', 'medium', 'low']:
            writer.writerow([sev.capitalize(), data['defects_by_severity'][sev]])
        writer.writerow([])

        if data['component_costs']:
            writer.writerow(['COST BY COMPONENT'])
            writer.writerow(['Component', 'Occurrences', 'Repair Cost (€)'])
            for item in data['component_costs']:
                writer.writerow([item['component'], item['count'], item['cost']])
            writer.writerow([])

        writer.writerow(['BIKES SUMMARY'])
        writer.writerow(['Bike Model', 'Sessions', 'Avg Minutes', 'Defects'])
        for b in data['bikes_summary']:
            writer.writerow([str(b['bike']), b['sessions'], b['avg_minutes'], b['defects']])

        return response


class WeeklyReportView(SupervisorRequiredMixin, View):
    def get(self, request):
        week_offset = int(request.GET.get('week', 0))
        today = timezone.now().date()
        start_of_week = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(weeks=week_offset)
        end_of_week = start_of_week + datetime.timedelta(days=6)

        data = _get_report_data(start_of_week, end_of_week)
        data['start_date'] = start_of_week
        data['end_date'] = end_of_week
        data['week_offset'] = week_offset
        data['prev_week'] = week_offset + 1
        data['next_week'] = week_offset - 1 if week_offset > 0 else None

        return render(request, 'reports/weekly.html', data)


class MonthlyReportView(SupervisorRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        last_day = calendar.monthrange(year, month)[1]
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, last_day)

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        data = _get_report_data(start_date, end_date)
        data['start_date'] = start_date
        data['end_date'] = end_date
        data['month'] = month
        data['year'] = year
        data['month_name'] = start_date.strftime('%B %Y')
        data['prev_month'] = prev_month
        data['prev_year'] = prev_year
        data['next_month'] = next_month
        data['next_year'] = next_year

        return render(request, 'reports/monthly.html', data)
