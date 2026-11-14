from django.urls import path
from .views import (
    ListingListCreateView,
    ListingDetailView,
    MyListingsView,
    ListingPhotoUploadView,
    ListingPhotoDeleteView,
)

app_name = 'listings'

urlpatterns = [
    path('', ListingListCreateView.as_view(), name='list_create'),
    path('my/', MyListingsView.as_view(), name='my_listings'),
    path('<int:pk>/', ListingDetailView.as_view(), name='detail'),
    path('<int:listing_id>/photos/', ListingPhotoUploadView.as_view(), name='photo_upload'),
    path('photos/<int:pk>/', ListingPhotoDeleteView.as_view(), name='photo_delete'),
]
