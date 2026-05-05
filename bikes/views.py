from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import BikeModel, Component
from .forms import BikeModelForm, ComponentForm


class LeadRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lead_or_above:
            messages.error(request, 'Access restricted to Team Leads and Supervisors.')
            return redirect('assembly:dashboard')
        return super().dispatch(request, *args, **kwargs)


class BikeListView(LoginRequiredMixin, ListView):
    model = BikeModel
    template_name = 'bikes/list.html'
    context_object_name = 'bikes'


class BikeDetailView(LoginRequiredMixin, DetailView):
    model = BikeModel
    template_name = 'bikes/detail.html'
    context_object_name = 'bike'


class BikeCreateView(LeadRequiredMixin, CreateView):
    model = BikeModel
    form_class = BikeModelForm
    template_name = 'bikes/form.html'
    success_url = reverse_lazy('bikes:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'New Bike Model'
        return ctx


class BikeUpdateView(LeadRequiredMixin, UpdateView):
    model = BikeModel
    form_class = BikeModelForm
    template_name = 'bikes/form.html'
    success_url = reverse_lazy('bikes:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit {self.object}'
        return ctx


class ComponentCreateView(LeadRequiredMixin, CreateView):
    model = Component
    form_class = ComponentForm
    template_name = 'bikes/component_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['bike'] = get_object_or_404(BikeModel, pk=self.kwargs['bike_pk'])
        return ctx

    def form_valid(self, form):
        bike = get_object_or_404(BikeModel, pk=self.kwargs['bike_pk'])
        form.instance.bike_model = bike
        messages.success(self.request, 'Component added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bikes:detail', kwargs={'pk': self.kwargs['bike_pk']})


class ComponentDeleteView(LeadRequiredMixin, DeleteView):
    model = Component
    template_name = 'bikes/component_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('bikes:detail', kwargs={'pk': self.object.bike_model.pk})
