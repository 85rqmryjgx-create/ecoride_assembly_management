from django import forms
from .models import Defect, DefectComponent


class DefectForm(forms.ModelForm):
    class Meta:
        model = Defect
        fields = ['session', 'defect_type', 'component', 'severity', 'description', 'step_note', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'step_note': forms.TextInput(attrs={'placeholder': 'e.g. Step 3 – handlebar alignment, rear brake, etc.'}),
            'photo': forms.FileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
        }
        labels = {
            'step_note': 'Related Step / Note (optional)',
            'component': 'Affected Component',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['step_note'].required = False
        self.fields['photo'].required = False
        self.fields['component'].required = False
        components = DefectComponent.objects.filter(active=True).values_list('code', 'name')
        self.fields['component'].choices = [('', '— Select component —')] + list(components)


class DefectResolveForm(forms.ModelForm):
    class Meta:
        model = Defect
        fields = ['resolution_description', 'resolution_minutes']
        widgets = {
            'resolution_description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'resolution_description': 'Descrição da resolução',
            'resolution_minutes': 'Tempo gasto para resolver (minutos)',
        }
