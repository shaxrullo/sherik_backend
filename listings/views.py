from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Listing, ListingPhoto
from .serializers import (
    ListingListSerializer,
    ListingDetailSerializer,
    ListingCreateUpdateSerializer,
    ListingPhotoUploadSerializer,
    ListingPhotoSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .pagination import StandardResultsSetPagination
from .filters import ListingFilter


@extend_schema(
    tags=['Listings'],
    summary="E'lonlar ro'yxati va yangi e'lon yaratish",
    description="Faol va tasdiqlangan (approved) e'lonlar ro'yxati. Filtrlar, qidiruv va sahifalash mavjud.",
)
class ListingListCreateView(generics.ListCreateAPIView):
    """E'lonlar ro'yxati (ommaviy) va yangi e'lon yaratish (avtorizatsiyalangan)."""

    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ListingFilter
    search_fields = [
        'title',
        'description',
        'address_line',
        'city__name',
        'district__name',
        'near_subway',
    ]
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ListingCreateUpdateSerializer
        return ListingListSerializer

    def get_queryset(self):
        # Ommaviy ro'yxatda faqat faol va tasdiqlangan (approved) hamda muallifi bloklanmagan e'lonlar chiqadi
        return (
            Listing.objects.filter(
                status=Listing.Status.ACTIVE,
                moderation_status=Listing.ModerationStatus.APPROVED,
                author__is_active=True,
            )
            .select_related('author', 'city', 'district')
            .prefetch_related('photos')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()

        # Javobda to'liq ma'lumotni chiqarish
        detail_serializer = ListingDetailSerializer(listing, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Listings'],
    summary="Bitta e'lonni ko'rish, tahrirlash va o'chirish",
    description="Faqat e'lon egasi uni tahrirlashi (PUT, PATCH) va o'chirishi (DELETE) mumkin.",
)
class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Bitta e'lon bilan ishlash viewsi."""

    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ListingCreateUpdateSerializer
        return ListingDetailSerializer

    def get_queryset(self):
        return (
            Listing.objects.all()
            .select_related('author', 'city', 'district')
            .prefetch_related('photos')
        )

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        # Agar e'lon approved bo'lmasa, uni faqat egasi yoki xodim (admin/moderator) ko'ra oladi
        is_owner_or_staff = user.is_authenticated and (user == obj.author or user.is_staff)
        if obj.moderation_status != Listing.ModerationStatus.APPROVED and not is_owner_or_staff:
            raise NotFound("E'lon topilmadi yoki moderatsiyadan o'tmagan.")

        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        detail_serializer = ListingDetailSerializer(updated_instance, context={'request': request})
        return Response(detail_serializer.data)


@extend_schema(
    tags=['Listings'],
    summary="Mening e'lonlarim",
    description="Avtorizatsiyadan o'tgan foydalanuvchining barcha e'lonlari (pending, approved, rejected, closed).",
)
class MyListingsView(generics.ListAPIView):
    """Foydalanuvchining o'z e'lonlari ro'yxati."""

    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Listing.objects.none()
        return (
            Listing.objects.filter(author=self.request.user)
            .select_related('author', 'city', 'district')
            .prefetch_related('photos')
            .order_by('-created_at')
        )


@extend_schema(
    tags=['Listings'],
    summary="E'longa rasm yuklash",
    description="Faqat e'lon egasi o'z e'loniga rasm yuklay oladi.",
)
class ListingPhotoUploadView(generics.CreateAPIView):
    """E'longa rasm yuklash viewsi."""

    serializer_class = ListingPhotoUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        listing_id = self.kwargs.get('listing_id')
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise NotFound("E'lon topilmadi.")

        # Huquqni tekshirish: faqat e'lon egasi rasm yuklashi mumkin
        if listing.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("Siz faqat o'zingizning e'loningizga rasm yuklay olasiz.")

        serializer.save(listing=listing)


@extend_schema(
    tags=['Listings'],
    summary="E'lon rasmini o'chirish",
    description="Faqat e'lon egasi yoki moderator rasmni o'chira oladi.",
)
class ListingPhotoDeleteView(generics.DestroyAPIView):
    """E'lon rasmini o'chirish viewsi."""

    queryset = ListingPhoto.objects.select_related('listing')
    serializer_class = ListingPhotoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
