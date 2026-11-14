from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Report
from .serializers import ReportSerializer
from listings.pagination import StandardResultsSetPagination


@extend_schema(
    tags=['Reports'],
    summary="Shikoyat yuborish (Soxta e'lon yoki firibgarlarga qarshi)",
    description="Foydalanuvchi e'lon yoki boshqa foydalanuvchi ustidan shikoyat yuborishi mumkin.",
    responses={
        201: OpenApiResponse(description="Shikoyat muvaffaqiyatli qabul qilindi"),
        400: OpenApiResponse(description="Validatsiya xatosi"),
    }
)
class ReportCreateView(generics.CreateAPIView):
    """Shikoyat yuborish viewsi."""

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        return Response(
            {
                'message': "Shikoyatingiz qabul qilindi va moderatorlar tomonidan ko'rib chiqiladi.",
                'data': ReportSerializer(report, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=['Reports'],
    summary="Mening yuborgan shikoyatlarim",
    description="Foydalanuvchi o'zi yuborgan shikoyatlar holatini kuzatishi mumkin.",
)
class MyReportsListView(generics.ListAPIView):
    """Foydalanuvchining o'z shikoyatlari ro'yxati."""

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Report.objects.none()
        return (
            Report.objects.filter(reporter=self.request.user)
            .select_related('reported_listing', 'reported_user')
            .order_by('-created_at')
        )
