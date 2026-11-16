from django.urls import path
from .views import (
    FavoriteListView,
    FavoriteCreateView,
    FavoriteRemoveView,
    FavoriteToggleView,
    FavoriteClearView,
)

app_name = 'favorites'

urlpatterns = [
    path('', FavoriteListView.as_view(), name='list'),
    path('add/', FavoriteCreateView.as_view(), name='add'),
    path('toggle/', FavoriteToggleView.as_view(), name='toggle'),
    path('clear/', FavoriteClearView.as_view(), name='clear'),
    path('<int:listing_id>/', FavoriteRemoveView.as_view(), name='remove'),
]
