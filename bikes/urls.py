from django.urls import path
from . import views

app_name = 'bikes'

urlpatterns = [
    path('', views.BikeListView.as_view(), name='list'),
    path('new/', views.BikeCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BikeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.BikeUpdateView.as_view(), name='update'),
    path('<int:bike_pk>/components/new/', views.ComponentCreateView.as_view(), name='component_create'),
    path('components/<int:pk>/delete/', views.ComponentDeleteView.as_view(), name='component_delete'),
]
