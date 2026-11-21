from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from users.views_admin import AdminStatsView

# Admin index uchun statistika kontekstini qo'shish
original_admin_index = admin.site.index


def custom_admin_index(request, extra_context=None):
    from users.models import User
    from listings.models import Listing
    from reports.models import Report

    extra_context = extra_context or {}
    try:
        seven_days_ago = timezone.now() - timedelta(days=7)
        extra_context['stats'] = {
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'blocked_users': User.objects.filter(is_active=False).count(),
            'active_listings': Listing.objects.filter(
                status=Listing.Status.ACTIVE,
                moderation_status=Listing.ModerationStatus.APPROVED
            ).count(),
            'pending_listings': Listing.objects.filter(
                moderation_status=Listing.ModerationStatus.PENDING
            ).count(),
            'new_reports': Report.objects.filter(status=Report.Status.NEW).count(),
            'last_7_days_listings': Listing.objects.filter(created_at__gte=seven_days_ago).count(),
            'last_7_days_users': User.objects.filter(date_joined__gte=seven_days_ago).count(),
        }
    except Exception as e:
        extra_context['stats'] = {}
    return original_admin_index(request, extra_context=extra_context)


admin.site.index = custom_admin_index
admin.site.site_header = "Sherik Topish — Moderatsiya va Boshqaruv Paneli"
admin.site.site_title = "Sherik Topish Admin"
admin.site.index_title = "Boshqaruv Paneli va Jonli Ko'rsatkichlar"

urlpatterns = [
    # Himoyalangan maxsus Admin panel manzili (.env orqali boshqariladi)
    path(settings.ADMIN_URL, admin.site.urls),

    # API Dokumentatsiya (Swagger & Redoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Admin API
    path('api/v1/admin/', include('users.urls_admin')),

    # API v1 ilovalar
    path('api/v1/auth/', include('users.urls_auth')),
    path('api/v1/users/', include('users.urls_users')),
    path('api/v1/listings/', include('listings.urls')),
    path('api/v1/favorites/', include('favorites.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/matching/', include('matching.urls')),

    # Telegram Bot Webhook
    path('api/v1/telegram-webhook/', include([
        path('', __import__('telegram_bot.views', fromlist=['TelegramWebhookView']).TelegramWebhookView.as_view(), name='telegram-webhook'),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
