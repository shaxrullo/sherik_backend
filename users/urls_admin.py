from django.urls import path
from .views_admin import (
    AdminStatsView,
    AdminListingsView,
    AdminListingApproveView,
    AdminListingRejectView,
    AdminListingDeleteView,
    AdminUsersView,
    AdminUserToggleVerifyView,
    AdminUserToggleBlockView,
    AdminReportsView,
    AdminReportUpdateStatusView,
    AdminSeedCitiesView,
)

app_name = 'admin_api'

urlpatterns = [
    # Statistika
    path('stats/', AdminStatsView.as_view(), name='stats'),

    # E'lonlar moderatsiyasi
    path('listings/', AdminListingsView.as_view(), name='listings'),
    path('listings/<int:pk>/approve/', AdminListingApproveView.as_view(), name='listing_approve'),
    path('listings/<int:pk>/reject/', AdminListingRejectView.as_view(), name='listing_reject'),
    path('listings/<int:pk>/', AdminListingDeleteView.as_view(), name='listing_delete'),

    # Foydalanuvchilar
    path('users/', AdminUsersView.as_view(), name='users'),
    path('users/<int:pk>/toggle-verify/', AdminUserToggleVerifyView.as_view(), name='user_toggle_verify'),
    path('users/<int:pk>/toggle-block/', AdminUserToggleBlockView.as_view(), name='user_toggle_block'),

    # Shikoyatlar
    path('reports/', AdminReportsView.as_view(), name='reports'),
    path('reports/<int:pk>/status/', AdminReportUpdateStatusView.as_view(), name='report_update_status'),

    # Shaharlar seed (bir marta ishlatiladi)
    path('seed-cities/', AdminSeedCitiesView.as_view(), name='seed_cities'),
]

