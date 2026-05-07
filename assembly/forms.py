from django import forms
from django.contrib.auth import get_user_model
from .models import AssemblyProcess, AssemblyStep, AssemblySession, StepExecution, ProductionOrder

User = get_user_model()


class ProcessForm(forms.ModelForm):
    class Meta:
        model = AssemblyProcess
        fields = ['bike_model', 'name', 'description', 'active']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class StepForm(forms.ModelForm):
    class Meta:
        model = AssemblyStep
        fields = ['name', 'description', 'order', 'estimated_minutes']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}


class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = AssemblySession
        fields = ['bike_model', 'process', 'worker', 'order_number', 'serial_number', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['process'].queryset = AssemblyProcess.objects.filter(active=True).select_related('bike_model')
        self.fields['worker'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['worker'].required = True
        self.fields['worker'].label = 'Assigned Worker'


class SessionEditForm(forms.ModelForm):
    class Meta:
        model = AssemblySession
        fields = ['order_number', 'serial_number', 'notes', 'status']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}


class StepExecutionForm(forms.ModelForm):
    class Meta:
        model = StepExecution
        fields = ['actual_minutes', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['order_number', 'bike_model', 'quantity', 'target_date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'order_number': 'Order Number',
            'bike_model': 'Bike Model',
            'quantity': 'Total Units',
            'target_date': 'Target Date (optional)',
        }
