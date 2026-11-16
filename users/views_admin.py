from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.models import User
from listings.models import Listing
from reports.models import Report


class AdminListingSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    author_name = serializers.SerializerMethodField()
    author_phone = serializers.CharField(source='author.phone_number', read_only=True)
    author_email = serializers.CharField(source='author.email', read_only=True)
    author_verified = serializers.BooleanField(source='author.is_verified', read_only=True)
    main_photo = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'price',
            'listing_type',
            'gender_preference',
            'capacity',
            'city_name',
            'district_name',
            'address_line',
            'status',
            'moderation_status',
            'rejection_reason',
            'created_at',
            'updated_at',
            'author_id',
            'author_name',
            'author_phone',
            'author_email',
            'author_verified',
            'main_photo',
        ]

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name or ''}".strip() or "Noma'lum"

    def get_main_photo(self, obj):
        photos = list(obj.photos.all())
        if not photos:
            return None
        main = next((p for p in photos if p.is_main), photos[0])
        request = self.context.get('request')
        if request and main.image:
            return request.build_absolute_uri(main.image.url)
        return main.image.url if main.image else None


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    city_name = serializers.CharField(source='city.name', read_only=True)
    listings_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'is_verified',
            'is_active',
            'is_staff',
            'is_superuser',
            'city_name',
            'date_joined',
            'listings_count',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name or ''}".strip() or obj.email


class AdminReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.SerializerMethodField()
    reporter_email = serializers.CharField(source='reporter.email', read_only=True)
    reported_listing_title = serializers.CharField(source='reported_listing.title', read_only=True)
    reported_user_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id',
            'reason',
            'description',
            'status',
            'admin_notes',
            'created_at',
            'reporter_id',
            'reporter_name',
            'reporter_email',
            'reported_listing_id',
            'reported_listing_title',
            'reported_user_id',
            'reported_user_name',
        ]

    def get_reporter_name(self, obj):
        if not obj.reporter:
            return "Anonim"
        return f"{obj.reporter.first_name} {obj.reporter.last_name or ''}".strip()

    def get_reported_user_name(self, obj):
        if not obj.reported_user:
            return None
        return f"{obj.reported_user.first_name} {obj.reported_user.last_name or ''}".strip()


# --- VIEWS ---

@extend_schema(tags=['Admin Moderatsiya'], summary="Platforma statistikasi")
class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        return Response({
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'blocked_users': User.objects.filter(is_active=False).count(),
            'active_listings': Listing.objects.filter(
                status=Listing.Status.ACTIVE,
                moderation_status=Listing.ModerationStatus.APPROVED,
            ).count(),
            'pending_listings': Listing.objects.filter(
                moderation_status=Listing.ModerationStatus.PENDING,
            ).count(),
            'rejected_listings': Listing.objects.filter(
                moderation_status=Listing.ModerationStatus.REJECTED,
            ).count(),
            'new_reports': Report.objects.filter(status=Report.Status.NEW).count(),
            'in_review_reports': Report.objects.filter(status=Report.Status.IN_REVIEW).count(),
            'last_7_days_listings': Listing.objects.filter(created_at__gte=seven_days_ago).count(),
            'last_7_days_users': User.objects.filter(date_joined__gte=seven_days_ago).count(),
        })


@extend_schema(tags=['Admin Moderatsiya'], summary="E'lonlar ro'yxati (Moderatsiya uchun)")
class AdminListingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = (
            Listing.objects.all()
            .select_related('city', 'district', 'author')
            .prefetch_related('photos')
            .order_by('-created_at')
        )

        mod_status = request.query_params.get('moderation_status')
        if mod_status and mod_status != 'all':
            qs = qs.filter(moderation_status=mod_status)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(author__first_name__icontains=search)
                | Q(author__email__icontains=search)
                | Q(author__phone_number__icontains=search)
            )

        limit = min(int(request.query_params.get('limit', 50)), 100)
        serializer = AdminListingSerializer(qs[:limit], many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema(tags=['Admin Moderatsiya'], summary="E'lonni tasdiqlash (Approve)")
class AdminListingApproveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            listing = Listing.objects.get(pk=pk)
        except Listing.DoesNotExist:
            return Response({'error': "E'lon topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        listing.moderation_status = Listing.ModerationStatus.APPROVED
        listing.status = Listing.Status.ACTIVE
        listing.rejection_reason = ''
        listing.save(update_fields=['moderation_status', 'status', 'rejection_reason', 'updated_at'])

        return Response({
            'message': "E'lon muvaffaqiyatli tasdiqlandi",
            'listing': AdminListingSerializer(listing, context={'request': request}).data,
        })


@extend_schema(tags=['Admin Moderatsiya'], summary="E'lonni rad etish (Reject)")
class AdminListingRejectView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            listing = Listing.objects.get(pk=pk)
        except Listing.DoesNotExist:
            return Response({'error': "E'lon topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '').strip()
        listing.moderation_status = Listing.ModerationStatus.REJECTED
        listing.rejection_reason = reason
        listing.save(update_fields=['moderation_status', 'rejection_reason', 'updated_at'])

        return Response({
            'message': "E'lon rad etildi",
            'listing': AdminListingSerializer(listing, context={'request': request}).data,
        })


@extend_schema(tags=['Admin Moderatsiya'], summary="E'lonni o'chirish (Delete)")
class AdminListingDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            listing = Listing.objects.get(pk=pk)
        except Listing.DoesNotExist:
            return Response({'error': "E'lon topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        listing.delete()
        return Response({'message': "E'lon muvaffaqiyatli o'chirildi"})


@extend_schema(tags=['Admin Moderatsiya'], summary="Foydalanuvchilar ro'yxati")
class AdminUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = (
            User.objects.all()
            .annotate(listings_count=Count('listings'))
            .select_related('city')
            .order_by('-date_joined')
        )

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone_number__icontains=search)
            )

        is_verified = request.query_params.get('is_verified')
        if is_verified is not None and is_verified != '':
            qs = qs.filter(is_verified=is_verified.lower() == 'true')

        is_active = request.query_params.get('is_active')
        if is_active is not None and is_active != '':
            qs = qs.filter(is_active=is_active.lower() == 'true')

        limit = min(int(request.query_params.get('limit', 50)), 100)
        serializer = AdminUserSerializer(qs[:limit], many=True)
        return Response(serializer.data)


@extend_schema(tags=['Admin Moderatsiya'], summary="Foydalanuvchi tasdiqlanganlik holatini o'zgartirish")
class AdminUserToggleVerifyView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': "Foydalanuvchi topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = not user.is_verified
        user.save(update_fields=['is_verified'])

        return Response({
            'message': f"Foydalanuvchi {'tasdiqlandi' if user.is_verified else 'tasdiqlanmagan holatga o‘tkazildi'}",
            'is_verified': user.is_verified,
        })


@extend_schema(tags=['Admin Moderatsiya'], summary="Foydalanuvchini bloklash / ochish")
class AdminUserToggleBlockView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': "Foydalanuvchi topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if user.is_superuser:
            return Response({'error': "Superadminga ta'sir o'tkazib bo'lmaydi"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        return Response({
            'message': f"Foydalanuvchi {'faollashtirildi' if user.is_active else 'bloklandi'}",
            'is_active': user.is_active,
        })


@extend_schema(tags=['Admin Moderatsiya'], summary="Shikoyatlar ro'yxati")
class AdminReportsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = (
            Report.objects.all()
            .select_related('reporter', 'reported_listing', 'reported_user')
            .order_by('-created_at')
        )

        rep_status = request.query_params.get('status')
        if rep_status and rep_status != 'all':
            qs = qs.filter(status=rep_status)

        limit = min(int(request.query_params.get('limit', 50)), 100)
        serializer = AdminReportSerializer(qs[:limit], many=True)
        return Response(serializer.data)


@extend_schema(tags=['Admin Moderatsiya'], summary="Shikoyat holatini o'zgartirish")
class AdminReportUpdateStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({'error': "Shikoyat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in [Report.Status.NEW, Report.Status.IN_REVIEW, Report.Status.RESOLVED, Report.Status.DISMISSED]:
            return Response({'error': "Noto'g'ri status"}, status=status.HTTP_400_BAD_REQUEST)

        report.status = new_status
        if 'admin_notes' in request.data:
            report.admin_notes = request.data['admin_notes']
        report.save(update_fields=['status', 'admin_notes'])

        return Response({
            'message': "Shikoyat holati yangilandi",
            'report': AdminReportSerializer(report).data,
        })
