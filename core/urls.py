from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import FileResponse
from . import setup_view
import os


def service_worker(request):
    path_ = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    return FileResponse(open(path_, 'rb'), content_type='application/javascript')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='service_worker'),
    path('', RedirectView.as_view(url='/assembly/', permanent=False), name='home'),
    path('accounts/', include('accounts.urls')),
    path('bikes/', include('bikes.urls')),
    path('assembly/', include('assembly.urls')),
    path('defects/', include('defects.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('administration.urls')),
    path('init-setup/', setup_view.run_setup, name='setup'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
