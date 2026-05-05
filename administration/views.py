from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import AppSettings
from .forms import UserCreateForm, UserEditForm, UserPasswordForm, AppSettingsForm

User = get_user_model()


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_supervisor:
            messages.error(request, 'Access restricted to Supervisors.')
            return redirect('assembly:dashboard')
        return super().dispatch(request, *args, **kwargs)


class AdminIndexView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'administration/index.html', {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'settings': AppSettings.get(),
        })


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'administration/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.order_by('role', 'first_name', 'username')


class UserCreateView(AdminRequiredMixin, View):
    def get(self, request):
        form = UserCreateForm()
        return render(request, 'administration/user_form.html', {'form': form, 'title': 'Create User'})

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('administration:user_list')
        return render(request, 'administration/user_form.html', {'form': form, 'title': 'Create User'})


class UserEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        edit_user = get_object_or_404(User, pk=pk)
        form = UserEditForm(instance=edit_user)
        return render(request, 'administration/user_form.html', {
            'form': form,
            'title': f'Edit — {edit_user.get_full_name() or edit_user.username}',
            'edit_user': edit_user,
        })

    def post(self, request, pk):
        edit_user = get_object_or_404(User, pk=pk)
        form = UserEditForm(request.POST, instance=edit_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{edit_user.username}" updated.')
            return redirect('administration:user_list')
        return render(request, 'administration/user_form.html', {
            'form': form,
            'title': f'Edit — {edit_user.get_full_name() or edit_user.username}',
            'edit_user': edit_user,
        })


class UserPasswordView(AdminRequiredMixin, View):
    def get(self, request, pk):
        edit_user = get_object_or_404(User, pk=pk)
        form = UserPasswordForm()
        return render(request, 'administration/user_password.html', {
            'form': form,
            'edit_user': edit_user,
        })

    def post(self, request, pk):
        edit_user = get_object_or_404(User, pk=pk)
        form = UserPasswordForm(request.POST)
        if form.is_valid():
            edit_user.set_password(form.cleaned_data['new_password'])
            edit_user.save()
            messages.success(request, f'Password for "{edit_user.username}" updated.')
            return redirect('administration:user_list')
        return render(request, 'administration/user_password.html', {
            'form': form,
            'edit_user': edit_user,
        })


class ParametersView(AdminRequiredMixin, View):
    def get(self, request):
        form = AppSettingsForm(instance=AppSettings.get())
        return render(request, 'administration/parameters.html', {'form': form})

    def post(self, request):
        form = AppSettingsForm(request.POST, instance=AppSettings.get())
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('administration:parameters')
        return render(request, 'administration/parameters.html', {'form': form})
