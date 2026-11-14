from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    GoogleAuthView,
    UserProfileView,
    UserLifestylePreferenceView,
)

app_name = 'auth'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('google/', GoogleAuthView.as_view(), name='google_auth'),
    path('me/', UserProfileView.as_view(), name='me'),
    path('lifestyle/', UserLifestylePreferenceView.as_view(), name='lifestyle'),
]

