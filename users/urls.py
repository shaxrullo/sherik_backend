from django.urls import path, include

urlpatterns = [
    path('auth/', include('users.urls_auth')),
    path('users/', include('users.urls_users')),
]

