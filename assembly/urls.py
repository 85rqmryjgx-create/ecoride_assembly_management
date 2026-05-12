from django.urls import path
from . import views

app_name = 'assembly'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('processes/', views.ProcessListView.as_view(), name='process_list'),
    path('processes/new/', views.ProcessCreateView.as_view(), name='process_create'),
    path('processes/<int:pk>/', views.ProcessDetailView.as_view(), name='process_detail'),
    path('processes/<int:pk>/edit/', views.ProcessUpdateView.as_view(), name='process_update'),
    path('processes/<int:process_pk>/steps/new/', views.StepCreateView.as_view(), name='step_create'),
    path('steps/<int:pk>/edit/', views.StepUpdateView.as_view(), name='step_update'),
    path('steps/<int:pk>/delete/', views.StepDeleteView.as_view(), name='step_delete'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/new/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/finish/', views.SessionFinishView.as_view(), name='session_finish'),
    path('sessions/<int:pk>/edit/', views.SessionUpdateView.as_view(), name='session_update'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
    path('executions/<int:pk>/save/', views.StepExecutionSaveView.as_view(), name='execution_save'),
    path('executions/<int:pk>/update/', views.StepExecutionUpdateView.as_view(), name='execution_update'),
    path('executions/<int:pk>/reset/', views.StepExecutionResetView.as_view(), name='execution_reset'),
    path('orders/', views.ProductionOrderListView.as_view(), name='order_list'),
    path('orders/new/', views.ProductionOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.ProductionOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:order_pk>/units/<int:unit_pk>/', views.OrderUnitDetailView.as_view(), name='unit_detail'),
    path('orders/<int:order_pk>/units/<int:unit_pk>/add-session/', views.OrderUnitAddSessionView.as_view(), name='unit_add_session'),
    path('orders/<int:order_pk>/units/<int:unit_pk>/complete/', views.OrderUnitCompleteView.as_view(), name='unit_complete'),
    path('map/', views.AssemblyMapView.as_view(), name='map'),
    path('executions/<int:pk>/activate/', views.StepActivateView.as_view(), name='step_activate'),
    path('executions/<int:pk>/assign/', views.StepAssignWorkersView.as_view(), name='step_assign'),
]
