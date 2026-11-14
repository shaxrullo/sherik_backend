from django.urls import path
from .views import PublicUserDetailView

app_name = 'users'

urlpatterns = [
    path('<int:pk>/', PublicUserDetailView.as_view(), name='user_detail'),
]

