from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/assembly/', permanent=False), name='home'),
    path('accounts/', include('accounts.urls')),
    path('bikes/', include('bikes.urls')),
    path('assembly/', include('assembly.urls')),
    path('defects/', include('defects.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('administration.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
