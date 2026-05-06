from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.db.models import Count, Sum
from .models import AssemblyProcess, AssemblyStep, AssemblySession, StepExecution
from .forms import ProcessForm, StepForm, SessionCreateForm, SessionEditForm, StepExecutionForm
from bikes.models import BikeModel
from defects.models import Defect
from administration.models import AppSettings


class LeadRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lead_or_above:
            messages.error(request, 'Access restricted to Team Leads and Supervisors.')
            return redirect('assembly:dashboard')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        from django.shortcuts import render
        sessions_active = AssemblySession.objects.filter(
            status=AssemblySession.STATUS_IN_PROGRESS
        ).select_related('bike_model', 'worker')[:5]

        recent_defects = Defect.objects.filter(
            resolved_at__isnull=True
        ).select_related('session__bike_model', 'reported_by')[:5]

        now = timezone.now()
        today = now.date()
        iso = now.isocalendar()

        completed_today = AssemblySession.objects.filter(
            status=AssemblySession.STATUS_COMPLETED,
            finished_at__date=today,
        ).count()
        completed_this_week = AssemblySession.objects.filter(
            status=AssemblySession.STATUS_COMPLETED,
            finished_at__week=iso[1],
            finished_at__year=iso[0],
        ).count()
        completed_this_month = AssemblySession.objects.filter(
            status=AssemblySession.STATUS_COMPLETED,
            finished_at__year=today.year,
            finished_at__month=today.month,
        ).count()

        stats = {
            'sessions_today': AssemblySession.objects.filter(
                started_at__date=today
            ).count(),
            'open_defects': Defect.objects.filter(resolved_at__isnull=True).count(),
            'completed_this_week': completed_this_week,
            'bikes': BikeModel.objects.filter(active=True).count(),
        }

        app_settings = AppSettings.get()
        defect_alert = stats['open_defects'] >= app_settings.open_defect_alert_threshold

        def _goal(done, target):
            if not target:
                return None
            pct = min(100, round(done / target * 100))
            return {'done': done, 'target': target, 'pct': pct, 'met': done >= target}

        return render(request, 'assembly/dashboard.html', {
            'sessions_active': sessions_active,
            'recent_defects': recent_defects,
            'stats': stats,
            'defect_alert': defect_alert,
            'defect_alert_threshold': app_settings.open_defect_alert_threshold,
            'goal_daily': _goal(completed_today, app_settings.daily_production_target),
            'goal_weekly': _goal(completed_this_week, app_settings.weekly_production_target),
            'goal_monthly': _goal(completed_this_month, app_settings.monthly_production_target),
        })


class ProcessListView(LeadRequiredMixin, ListView):
    model = AssemblyProcess
    template_name = 'assembly/process_list.html'
    context_object_name = 'processes'

    def get_queryset(self):
        return AssemblyProcess.objects.select_related('bike_model').annotate(
            step_count=Count('steps')
        )


class ProcessDetailView(LeadRequiredMixin, DetailView):
    model = AssemblyProcess
    template_name = 'assembly/process_detail.html'
    context_object_name = 'process'


class ProcessCreateView(LeadRequiredMixin, CreateView):
    model = AssemblyProcess
    form_class = ProcessForm
    template_name = 'assembly/process_form.html'
    success_url = reverse_lazy('assembly:process_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'New Process'
        return ctx


class ProcessUpdateView(LeadRequiredMixin, UpdateView):
    model = AssemblyProcess
    form_class = ProcessForm
    template_name = 'assembly/process_form.html'
    success_url = reverse_lazy('assembly:process_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Process'
        return ctx


class StepCreateView(LeadRequiredMixin, CreateView):
    model = AssemblyStep
    form_class = StepForm
    template_name = 'assembly/step_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['process'] = get_object_or_404(AssemblyProcess, pk=self.kwargs['process_pk'])
        return ctx

    def form_valid(self, form):
        process = get_object_or_404(AssemblyProcess, pk=self.kwargs['process_pk'])
        form.instance.process = process
        messages.success(self.request, 'Step added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('assembly:process_detail', kwargs={'pk': self.kwargs['process_pk']})


class StepUpdateView(LeadRequiredMixin, UpdateView):
    model = AssemblyStep
    form_class = StepForm
    template_name = 'assembly/step_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['process'] = self.object.process
        return ctx

    def get_success_url(self):
        return reverse('assembly:process_detail', kwargs={'pk': self.object.process.pk})


class StepDeleteView(LeadRequiredMixin, DeleteView):
    model = AssemblyStep
    template_name = 'assembly/step_confirm_delete.html'

    def get_success_url(self):
        return reverse('assembly:process_detail', kwargs={'pk': self.object.process.pk})


class SessionListView(LoginRequiredMixin, ListView):
    model = AssemblySession
    template_name = 'assembly/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 30

    def get_queryset(self):
        qs = AssemblySession.objects.select_related('bike_model', 'process', 'worker')
        if self.request.user.is_worker:
            qs = qs.filter(worker=self.request.user)

        status = self.request.GET.get('status', '')
        if status in (AssemblySession.STATUS_IN_PROGRESS, AssemblySession.STATUS_COMPLETED, AssemblySession.STATUS_PAUSED):
            qs = qs.filter(status=status)

        bike = self.request.GET.get('bike', '')
        if bike:
            qs = qs.filter(bike_model_id=bike)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                models.Q(order_number__icontains=q) |
                models.Q(serial_number__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['bike_filter'] = self.request.GET.get('bike', '')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['bike_models'] = BikeModel.objects.filter(active=True)
        return ctx


class SessionCreateView(LeadRequiredMixin, CreateView):
    model = AssemblySession
    form_class = SessionCreateForm
    template_name = 'assembly/session_form.html'

    def form_valid(self, form):
        session = form.save()
        for step in session.process.steps.all():
            StepExecution.objects.create(session=session, step=step)
        messages.success(self.request, 'Assembly session started!')
        return redirect('assembly:session_detail', pk=session.pk)


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = AssemblySession
    template_name = 'assembly/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['executions'] = self.object.step_executions.select_related('step').prefetch_related('defects')
        ctx['defects'] = self.object.defects.select_related('reported_by', 'step_execution__step')
        ctx['execution_form'] = StepExecutionForm()
        return ctx


class SessionFinishView(LeadRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(AssemblySession, pk=pk)
        session.status = AssemblySession.STATUS_COMPLETED
        session.finished_at = timezone.now()
        session.save()
        messages.success(request, 'Assembly completed!')
        return redirect('assembly:session_detail', pk=pk)


class SessionUpdateView(LeadRequiredMixin, UpdateView):
    model = AssemblySession
    form_class = SessionEditForm
    template_name = 'assembly/session_edit.html'
    context_object_name = 'session'

    def get_success_url(self):
        return reverse('assembly:session_detail', kwargs={'pk': self.object.pk})


class SessionDeleteView(LeadRequiredMixin, DeleteView):
    model = AssemblySession
    template_name = 'assembly/session_confirm_delete.html'
    context_object_name = 'session'
    success_url = reverse_lazy('assembly:session_list')


class StepExecutionUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        execution = get_object_or_404(StepExecution, pk=pk)
        minutes = request.POST.get('actual_minutes')
        notes = request.POST.get('notes', '')
        if minutes:
            execution.actual_minutes = max(1, int(minutes))
            execution.notes = notes
            execution.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'minutes': execution.actual_minutes})
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Minutos inválidos'})
        return redirect('assembly:session_detail', pk=execution.session.pk)


class StepExecutionResetView(LeadRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        execution = get_object_or_404(StepExecution, pk=pk)
        session_pk = execution.session.pk
        execution.actual_minutes = None
        execution.finished_at = None
        execution.notes = ''
        execution.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('assembly:session_detail', pk=session_pk)


class StepExecutionSaveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.http import JsonResponse
        import datetime as dt
        execution = get_object_or_404(StepExecution, pk=pk)
        minutes = request.POST.get('actual_minutes')
        notes = request.POST.get('notes', '')
        if minutes:
            actual = max(1, int(minutes))
            execution.actual_minutes = actual
            execution.finished_at = timezone.now()
            execution.started_at = execution.finished_at - dt.timedelta(minutes=actual)
            execution.notes = notes
            execution.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'minutes': execution.actual_minutes})
            messages.success(request, f'Step "{execution.step.name}" saved.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid minutes'})
        return redirect('assembly:session_detail', pk=execution.session.pk)
