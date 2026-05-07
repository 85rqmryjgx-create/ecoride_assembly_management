from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def complete_profile(request):
    if not request.user.must_change_password:
        return redirect('assembly:dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        salary = request.POST.get('salary_monthly', '').strip()
        errors = {}

        if len(new_password) < 8:
            errors['new_password'] = 'Password must be at least 8 characters.'
        elif new_password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if salary:
            try:
                salary = float(salary.replace(',', '.'))
                if salary <= 0:
                    errors['salary_monthly'] = 'Enter a valid salary above 0.'
            except ValueError:
                errors['salary_monthly'] = 'Enter a valid number.'
        else:
            salary = None

        if not errors:
            user = request.user
            user.set_password(new_password)
            user.must_change_password = False
            if salary is not None:
                user.salary_monthly = salary
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Profile completed! Welcome to Ecoride Assembly.')
            return redirect('assembly:dashboard')

        return render(request, 'accounts/complete_profile.html', {'errors': errors, 'salary': salary or ''})

    return render(request, 'accounts/complete_profile.html', {'errors': {}, 'salary': ''})
