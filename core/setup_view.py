from django.http import HttpResponse
from django.contrib.auth import get_user_model

User = get_user_model()


def run_setup(request):
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse(
            "<h2>Setup already complete.</h2><p>A superuser already exists. This page is now inactive.</p>",
            status=403,
        )

    User.objects.create_superuser(
        username='admin',
        email='danilolima45@hotmail.com',
        password='Ecoride@2026',
        first_name='Admin',
        role='supervisor',
    )

    return HttpResponse("""
    <html><body style="font-family:sans-serif;max-width:500px;margin:60px auto;padding:20px;">
    <h2>✅ Superuser created successfully!</h2>
    <p><strong>Username:</strong> admin</p>
    <p><strong>Password:</strong> Ecoride@2026</p>
    <p><strong>Role:</strong> Supervisor</p>
    <hr>
    <p>👉 <a href="/accounts/login/">Go to login</a></p>
    <p style="color:#e53e3e;font-size:13px;">⚠️ Change your password after the first login in Settings → Users.</p>
    </body></html>
    """)
