from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.models import User
from listings.models import Listing
from reports.models import Report


@extend_schema(
    tags=['Admin Moderatsiya'],
    summary="Platforma statistikasi (Faqat Moderator / Admin uchun)",
    description="Foydalanuvchilar, e'lonlar, moderatsiya va shikoyatlar bo'yicha umumiy statistik ma'lumotlar.",
    responses={
        200: OpenApiResponse(description="Statistika muvaffaqiyatli qaytarildi"),
        403: OpenApiResponse(description="Ruxsat berilmagan (faqat is_staff foydalanuvchilar)"),
    }
)
class AdminStatsView(APIView):
    """Admin va Moderatorlar uchun umumiy tizim statistikasi."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        total_users = User.objects.count()
        verified_users = User.objects.filter(is_verified=True).count()
        blocked_users = User.objects.filter(is_active=False).count()

        active_listings = Listing.objects.filter(
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        ).count()
        pending_listings = Listing.objects.filter(
            moderation_status=Listing.ModerationStatus.PENDING,
        ).count()
        rejected_listings = Listing.objects.filter(
            moderation_status=Listing.ModerationStatus.REJECTED,
        ).count()

        new_reports = Report.objects.filter(status=Report.Status.NEW).count()
        in_review_reports = Report.objects.filter(status=Report.Status.IN_REVIEW).count()

        last_7_days_listings = Listing.objects.filter(created_at__gte=seven_days_ago).count()
        last_7_days_users = User.objects.filter(date_joined__gte=seven_days_ago).count()

        listings_by_city = list(
            Listing.objects.values('city__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'total_users': total_users,
            'verified_users': verified_users,
            'blocked_users': blocked_users,
            'active_listings': active_listings,
            'pending_listings': pending_listings,
            'rejected_listings': rejected_listings,
            'new_reports': new_reports,
            'in_review_reports': in_review_reports,
            'last_7_days_listings': last_7_days_listings,
            'last_7_days_users': last_7_days_users,
            'listings_by_city': listings_by_city,
        })

