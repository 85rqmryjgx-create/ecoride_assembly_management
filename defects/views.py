from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import Defect, DefectComponent
from .forms import DefectForm, DefectResolveForm
from assembly.models import AssemblySession, StepExecution


class DefectListView(LoginRequiredMixin, ListView):
    model = Defect
    template_name = 'defects/list.html'
    context_object_name = 'defects'
    paginate_by = 30

    def get_queryset(self):
        qs = Defect.objects.select_related(
            'session__bike_model', 'reported_by', 'step_execution__step'
        )
        status = self.request.GET.get('status', 'open')
        if status == 'open':
            qs = qs.filter(resolved_at__isnull=True)
        elif status == 'resolved':
            qs = qs.filter(resolved_at__isnull=False)

        severity = self.request.GET.get('severity', '')
        if severity in ('low', 'medium', 'high', 'critical'):
            qs = qs.filter(severity=severity)

        component = self.request.GET.get('component', '')
        if component:
            qs = qs.filter(component=component)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', 'open')
        ctx['severity_filter'] = self.request.GET.get('severity', '')
        ctx['component_filter'] = self.request.GET.get('component', '')
        ctx['components'] = DefectComponent.objects.filter(active=True)
        return ctx


class DefectDetailView(LoginRequiredMixin, DetailView):
    model = Defect
    template_name = 'defects/detail.html'
    context_object_name = 'defect'


class DefectCreateView(LoginRequiredMixin, CreateView):
    model = Defect
    form_class = DefectForm
    template_name = 'defects/form.html'

    def get_initial(self):
        initial = super().get_initial()
        if 'session_pk' in self.kwargs:
            initial['session'] = self.kwargs['session_pk']
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'session_pk' in self.kwargs:
            ctx['session'] = get_object_or_404(AssemblySession, pk=self.kwargs['session_pk'])
        return ctx

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Defect logged successfully.')
        if self.object.severity == Defect.SEVERITY_CRITICAL:
            self._notify_supervisors(self.object)
        return response

    def _notify_supervisors(self, defect):
        from accounts.models import User
        supervisors = list(
            User.objects.filter(role=User.ROLE_SUPERVISOR, is_active=True)
            .values_list('email', flat=True)
        )
        supervisors = [e for e in supervisors if e]
        if not supervisors:
            return
        session = defect.session
        subject = f'[CRITICAL DEFECT] {session.bike_model} — Session #{session.pk}'
        body = (
            f'A critical defect has been reported.\n\n'
            f'Bike Model : {session.bike_model}\n'
            f'Session    : #{session.pk}'
            + (f' · {session.order_number}' if session.order_number else '') + '\n'
            f'Type       : {defect.get_defect_type_display()}\n'
            f'Component  : {defect.component or "—"}\n'
            f'Reported by: {defect.reported_by}\n\n'
            f'Description:\n{defect.description}\n\n'
            f'Please log in to review and resolve this defect immediately.'
        )
        try:
            send_mail(subject, body, django_settings.DEFAULT_FROM_EMAIL, supervisors, fail_silently=True)
        except Exception:
            pass

    def get_success_url(self):
        if self.object.session:
            return reverse('assembly:session_detail', kwargs={'pk': self.object.session.pk})
        return reverse('defects:list')


class SessionStepsAPIView(LoginRequiredMixin, View):
    def get(self, request, session_pk):
        executions = StepExecution.objects.filter(
            session_id=session_pk
        ).select_related('step').order_by('step__order')
        data = [{'id': e.pk, 'label': f'{e.step.order}. {e.step.name}'} for e in executions]
        return JsonResponse({'steps': data})


class DefectResolveView(LoginRequiredMixin, View):
    def get(self, request, pk):
        defect = get_object_or_404(Defect, pk=pk)
        form = DefectResolveForm(instance=defect)
        from django.shortcuts import render
        return render(request, 'defects/resolve.html', {'defect': defect, 'form': form})

    def post(self, request, pk):
        defect = get_object_or_404(Defect, pk=pk)
        form = DefectResolveForm(request.POST, instance=defect)
        if form.is_valid():
            resolved = form.save(commit=False)
            resolved.resolved_at = timezone.now()
            resolved.resolved_by = request.user
            resolved.save()
            messages.success(request, 'Defect marked as resolved.')
            return redirect('assembly:session_detail', pk=defect.session.pk)
        from django.shortcuts import render
        return render(request, 'defects/resolve.html', {'defect': defect, 'form': form})
