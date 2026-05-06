import datetime
import calendar
import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, Avg, FloatField
from django.db.models.functions import Coalesce

from assembly.models import AssemblySession, StepExecution
from defects.models import Defect, DefectComponent
from bikes.models import BikeModel
from administration.models import AppSettings
from accounts.models import User


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
        writer.writerow([f'Labor Rate: Kr{data["labor_rate"]}/h'])
        writer.writerow([])

        writer.writerow(['SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Assemblies Completed', data['total_sessions']])
        writer.writerow(['Total Assembly Minutes', data['total_assembly_minutes']])
        writer.writerow(['Total Defects', data['total_defects']])
        writer.writerow(['Open Defects', data['open_defects']])
        writer.writerow(['Repair Minutes', data['total_resolution_minutes']])
        writer.writerow(['Assembly Labor Cost (Kr)', data['assembly_labor_cost']])
        writer.writerow(['Defect Repair Cost (Kr)', data['defect_repair_cost']])
        writer.writerow(['Cost per Unit (Kr)', data['cost_per_unit']])
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
            writer.writerow(['Component', 'Occurrences', 'Repair Cost (Kr)'])
            for item in data['component_costs']:
                writer.writerow([item['component'], item['count'], item['cost']])
            writer.writerow([])

        writer.writerow(['BIKES SUMMARY'])
        writer.writerow(['Bike Model', 'Sessions', 'Avg Minutes', 'Defects'])
        for b in data['bikes_summary']:
            writer.writerow([str(b['bike']), b['sessions'], b['avg_minutes'], b['defects']])

        return response


def _generate_recommendations(defects, total, resolved, component_stats, type_stats, severity_stats, bike_stats, labor_rate):
    recs = []
    if total == 0:
        return recs

    open_count = total - resolved
    open_rate = open_count / total

    if open_rate > 0.3:
        recs.append({
            'level': 'critical',
            'icon': '🔴',
            'title': 'High unresolved defect rate',
            'body': f'{round(open_rate*100)}% of defects ({open_count}) are still open. Escalate the resolution process immediately.',
        })

    for s in severity_stats:
        if s['severity'] in ('critical', 'high') and s['count'] / total > 0.25:
            recs.append({
                'level': 'high',
                'icon': '🟠',
                'title': f'Elevated {s["severity"]} severity defects',
                'body': f'{s["count"]} {s["severity"]}-severity defects represent {round(s["count"]/total*100)}% of all issues. Immediate quality review recommended.',
            })
            break

    for s in type_stats:
        if s['count'] / total > 0.5:
            if s['defect_type'] == 'manufacturing':
                recs.append({
                    'level': 'high',
                    'icon': '🏭',
                    'title': 'Manufacturing defects dominate',
                    'body': f'{s["count"]} manufacturing defects ({round(s["count"]/total*100)}% of total). Consider a supplier quality audit or incoming inspection.',
                })
            elif s['defect_type'] == 'assembly':
                recs.append({
                    'level': 'medium',
                    'icon': '🔧',
                    'title': 'Assembly issues dominate',
                    'body': f'{s["count"]} assembly defects ({round(s["count"]/total*100)}% of total). Review process instructions and consider targeted worker training.',
                })

    for s in component_stats[:3]:
        if s['count'] >= 3:
            cost = round((s.get('repair_minutes') or 0) / 60 * labor_rate, 2)
            if s['component'] in ('motor', 'battery', 'electronics'):
                recs.append({
                    'level': 'high',
                    'icon': '⚡',
                    'title': f'Recurring {s["component"]} failures',
                    'body': f'{s["count"]} {s["component"]} defects — Kr {cost} in repair cost. Verify supplier specs and incoming component testing.',
                })
            elif s['component'] in ('brakes', 'frame'):
                recs.append({
                    'level': 'critical',
                    'icon': '⚠️',
                    'title': f'Safety-critical component failing: {s["component"]}',
                    'body': f'{s["count"]} {s["component"]} defects detected. This is a safety-critical component — immediate inspection of all units recommended.',
                })
            else:
                recs.append({
                    'level': 'medium',
                    'icon': '🔁',
                    'title': f'Repeated {s["component"]} defects',
                    'body': f'{s["count"]} occurrences — Kr {cost} in repair cost. Consider a targeted process improvement for this component.',
                })

    for s in bike_stats[:1]:
        if total >= 5 and s['count'] / total > 0.4:
            recs.append({
                'level': 'medium',
                'icon': '🚴',
                'title': f'Model "{s["bike"]}" generating most defects',
                'body': f'{s["count"]} of {total} defects ({round(s["count"]/total*100)}%) occur on this model. Review its assembly process and component specifications.',
            })

    if not recs:
        recs.append({
            'level': 'good',
            'icon': '✅',
            'title': 'No critical patterns detected',
            'body': 'Defect levels and distribution are within acceptable range for this period. Continue monitoring.',
        })

    return recs


class DefectAnalysisView(SupervisorRequiredMixin, View):
    def get(self, request):
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days - 1)
        labor_rate = float(AppSettings.get().labor_rate_per_hour)

        defects = Defect.objects.filter(
            reported_at__date__gte=start_date,
            reported_at__date__lte=end_date,
        ).select_related('session__bike_model', 'reported_by')

        total = defects.count()
        resolved = defects.filter(resolved_at__isnull=False).count()

        avg_repair = defects.filter(
            resolved_at__isnull=False, resolution_minutes__isnull=False
        ).aggregate(avg=Sum('resolution_minutes'))['avg'] or 0
        avg_repair_min = round(avg_repair / resolved, 1) if resolved else 0

        component_stats = []
        for comp in DefectComponent.objects.filter(active=True):
            group = defects.filter(component=comp.code)
            count = group.count()
            if count:
                minutes = group.filter(resolved_at__isnull=False).aggregate(
                    total=Sum('resolution_minutes'))['total'] or 0
                component_stats.append({
                    'component': comp.name,
                    'code': comp.code,
                    'count': count,
                    'repair_minutes': minutes,
                    'cost': round(minutes / 60 * labor_rate, 2),
                    'pct': round(count / total * 100) if total else 0,
                })
        component_stats.sort(key=lambda x: x['count'], reverse=True)

        type_stats = list(defects.values('defect_type').annotate(count=Count('id')).order_by('-count'))
        severity_stats = list(defects.values('severity').annotate(count=Count('id')).order_by('-count'))

        bike_stats = []
        for row in defects.values('session__bike_model__id', 'session__bike_model__brand', 'session__bike_model__name').annotate(count=Count('id')).order_by('-count')[:5]:
            bike_stats.append({
                'bike': f"{row['session__bike_model__brand']} {row['session__bike_model__name']}",
                'count': row['count'],
            })

        recommendations = _generate_recommendations(
            defects, total, resolved, component_stats, type_stats, severity_stats, bike_stats, labor_rate
        )

        total_repair_cost = round(sum(c['cost'] for c in component_stats), 2)

        return render(request, 'reports/defect_analysis.html', {
            'days': days,
            'start_date': start_date,
            'end_date': end_date,
            'total': total,
            'resolved': resolved,
            'open': total - resolved,
            'avg_repair_min': avg_repair_min,
            'total_repair_cost': total_repair_cost,
            'labor_rate': labor_rate,
            'component_stats': component_stats,
            'type_stats': type_stats,
            'severity_stats': severity_stats,
            'bike_stats': bike_stats,
            'recommendations': recommendations,
        })


class WorkerPerformanceView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_lead_or_above:
            messages.error(request, 'Access restricted to Team Leads and Supervisors.')
            return redirect('assembly:dashboard')

        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days - 1)

        workers = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')

        labor_rate = float(AppSettings.get().labor_rate_per_hour)
        performance = []

        for worker in workers:
            sessions = AssemblySession.objects.filter(
                worker=worker,
                started_at__date__gte=start_date,
                started_at__date__lte=end_date,
            )
            total = sessions.count()
            completed = sessions.filter(status=AssemblySession.STATUS_COMPLETED).count()

            total_minutes = StepExecution.objects.filter(
                session__in=sessions,
                actual_minutes__isnull=False,
            ).aggregate(total=Sum('actual_minutes'))['total'] or 0

            avg_minutes = round(total_minutes / completed, 1) if completed else 0

            defects_reported = Defect.objects.filter(
                reported_by=worker,
                reported_at__date__gte=start_date,
                reported_at__date__lte=end_date,
            ).count()

            open_defects = Defect.objects.filter(
                session__in=sessions,
                resolved_at__isnull=True,
            ).count()

            defect_rate = round(defects_reported / total, 2) if total else 0
            labor_cost = round((total_minutes / 60) * labor_rate, 2)

            if total > 0:
                performance.append({
                    'worker': worker,
                    'total_sessions': total,
                    'completed': completed,
                    'avg_minutes': avg_minutes,
                    'defects_reported': defects_reported,
                    'open_defects': open_defects,
                    'defect_rate': defect_rate,
                    'labor_cost': labor_cost,
                })

        performance.sort(key=lambda x: x['completed'], reverse=True)

        return render(request, 'reports/worker_performance.html', {
            'days': days,
            'start_date': start_date,
            'end_date': end_date,
            'performance': performance,
        })


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
