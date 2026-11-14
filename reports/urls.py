from django.urls import path
from .views import ReportCreateView, MyReportsListView

app_name = 'reports'

urlpatterns = [
    path('', ReportCreateView.as_view(), name='create'),
    path('my/', MyReportsListView.as_view(), name='my_reports'),
]
