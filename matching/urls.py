from django.urls import path
from .views import MatchingRecommendationsView, ListingMatchCheckView

app_name = 'matching'

urlpatterns = [
    path('recommendations/', MatchingRecommendationsView.as_view(), name='recommendations'),
    path('listings/<int:listing_id>/', ListingMatchCheckView.as_view(), name='listing_match_detail'),
]
