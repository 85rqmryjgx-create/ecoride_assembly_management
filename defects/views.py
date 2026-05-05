from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Defect
from .forms import DefectForm, DefectResolveForm
from assembly.models import AssemblySession, StepExecution


class DefectListView(LoginRequiredMixin, ListView):
    model = Defect
    template_name = 'defects/list.html'
    context_object_name = 'defects'

    def get_queryset(self):
        qs = Defect.objects.select_related(
            'session__bike_model', 'reported_by', 'step_execution__step'
        )
        status = self.request.GET.get('status', 'open')
        if status == 'open':
            qs = qs.filter(resolved_at__isnull=True)
        elif status == 'resolved':
            qs = qs.filter(resolved_at__isnull=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', 'open')
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
        messages.success(self.request, 'Defect logged successfully.')
        return super().form_valid(form)

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
