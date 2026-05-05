from django.urls import path
from . import views

app_name = 'defects'

urlpatterns = [
    path('', views.DefectListView.as_view(), name='list'),
    path('new/', views.DefectCreateView.as_view(), name='create'),
    path('new/<int:session_pk>/', views.DefectCreateView.as_view(), name='create_for_session'),
    path('<int:pk>/', views.DefectDetailView.as_view(), name='detail'),
    path('<int:pk>/resolve/', views.DefectResolveView.as_view(), name='resolve'),
    path('api/session-steps/<int:session_pk>/', views.SessionStepsAPIView.as_view(), name='session_steps_api'),
]
