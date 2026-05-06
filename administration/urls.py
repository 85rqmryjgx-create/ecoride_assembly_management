from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.AdminIndexView.as_view(), name='index'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/password/', views.UserPasswordView.as_view(), name='user_password'),
    path('parameters/', views.ParametersView.as_view(), name='parameters'),
    path('components/', views.ComponentListView.as_view(), name='component_list'),
    path('components/add/', views.ComponentCreateView.as_view(), name='component_create'),
    path('components/<int:pk>/edit/', views.ComponentEditView.as_view(), name='component_edit'),
]
