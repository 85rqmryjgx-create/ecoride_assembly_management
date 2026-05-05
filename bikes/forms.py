from django import forms
from .models import BikeModel, Component


class BikeModelForm(forms.ModelForm):
    class Meta:
        model = BikeModel
        fields = ['name', 'brand', 'year', 'description', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['name', 'category', 'part_number', 'quantity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
