from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from .models import AppSettings

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='Confirm Password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'is_active']
        labels = {
            'is_active': 'Active (can log in)',
        }


class UserPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='New Password', min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), label='Confirm Password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class AppSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = AppSettings
        fields = [
            'company_name', 'labor_rate_per_hour', 'open_defect_alert_threshold',
            'daily_production_target', 'weekly_production_target', 'monthly_production_target',
        ]
        labels = {
            'company_name': 'Company Name',
            'labor_rate_per_hour': 'Labor Rate (Kr/hour)',
            'open_defect_alert_threshold': 'Open Defect Alert Threshold',
            'daily_production_target': 'Daily Target (assemblies/day)',
            'weekly_production_target': 'Weekly Target (assemblies/week)',
            'monthly_production_target': 'Monthly Target (assemblies/month)',
        }
        help_texts = {
            'labor_rate_per_hour': 'Used to calculate financial impact of defects in reports.',
            'open_defect_alert_threshold': 'Dashboard shows a warning when open defects exceed this number.',
            'daily_production_target': 'Set 0 to hide daily goal from dashboard.',
            'weekly_production_target': 'Set 0 to hide weekly goal from dashboard.',
            'monthly_production_target': 'Set 0 to hide monthly goal from dashboard.',
        }
