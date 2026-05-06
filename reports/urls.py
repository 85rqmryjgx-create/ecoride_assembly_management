from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportIndexView.as_view(), name='index'),
    path('weekly/', views.WeeklyReportView.as_view(), name='weekly'),
    path('monthly/', views.MonthlyReportView.as_view(), name='monthly'),
    path('export/', views.ReportExportCSVView.as_view(), name='export'),
    path('defect-analysis/', views.DefectAnalysisView.as_view(), name='defect_analysis'),
    path('workers/', views.WorkerPerformanceView.as_view(), name='worker_performance'),
]
