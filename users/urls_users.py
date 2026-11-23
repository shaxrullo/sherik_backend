from django.urls import path
from .views import PublicUserDetailView, CityListView

app_name = 'users'

urlpatterns = [
    path('cities/', CityListView.as_view(), name='cities_list'),
    path('<int:pk>/', PublicUserDetailView.as_view(), name='user_detail'),
]

