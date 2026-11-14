from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Favorite
from .serializers import FavoriteListSerializer, FavoriteActionSerializer
from listings.pagination import StandardResultsSetPagination
from listings.models import Listing


@extend_schema(
    tags=['Favorites'],
    summary="Foydalanuvchining sevimli e'lonlari ro'yxati",
    description="Faqat avtorizatsiyadan o'tgan foydalanuvchining o'z sevimli e'lonlarini qaytaradi.",
)
class FavoriteListView(generics.ListAPIView):
    """Sevimli e'lonlar ro'yxati viewsi."""

    serializer_class = FavoriteListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Favorite.objects.none()
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related('listing', 'listing__author', 'listing__city', 'listing__district')
            .prefetch_related('listing__photos')
            .order_by('-created_at')
        )


@extend_schema(
    tags=['Favorites'],
    summary="Sevimlilarga e'lon qo'shish",
    description="E'lonni sevimlilar ro'yxatiga qo'shish.",
    request=FavoriteActionSerializer,
    responses={
        201: OpenApiResponse(description="E'lon sevimlilarga qo'shildi"),
        400: OpenApiResponse(description="E'lon topilmadi yoki noto'g'ri so'rov"),
    }
)
class FavoriteCreateView(generics.CreateAPIView):
    """Sevimlilarga qo'shish viewsi."""

    serializer_class = FavoriteActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {
                'message': "E'lon sevimlilarga muvaffaqiyatli qo'shildi.",
                'data': result,
            },
            status=status.HTTP_201_CREATED if result['created'] else status.HTTP_200_OK
        )


@extend_schema(
    tags=['Favorites'],
    summary="Sevimlilardan e'lonni olib tashlash",
    description="E'lon ID si bo'yicha uni sevimlilar ro'yxatidan o'chiradi.",
    responses={
        204: OpenApiResponse(description="E'lon sevimlilardan olib tashlandi"),
        404: OpenApiResponse(description="Sevimli e'lon topilmadi"),
    }
)
class FavoriteRemoveView(APIView):
    """E'lonni sevimlilardan olib tashlash viewsi."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, listing_id):
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            listing_id=listing_id,
        ).delete()

        if deleted_count == 0:
            raise NotFound("Ushbu e'lon sizning sevimlilaringiz ro'yxatida topilmadi.")

        return Response(
            {'message': "E'lon sevimlilar ro'yxatidan olib tashlandi."},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(
    tags=['Favorites'],
    summary="Sevimlilar holatini o'zgartirish (Toggle: qo'shish/o'chirish)",
    description="Agar e'lon sevimlilarda bo'lsa o'chiradi, bo'lmasa qo'shadi.",
    request=FavoriteActionSerializer,
    responses={
        200: OpenApiResponse(description="Holat muvaffaqiyatli o'zgartirildi"),
    }
)
class FavoriteToggleView(APIView):
    """Sevimli e'lonni toggle (yoqish/o'chirish) viewsi."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        listing_id = request.data.get('listing_id')
        if not listing_id:
            return Response(
                {'listing_id': ["listing_id kiritilishi shart."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            listing = Listing.objects.get(
                id=listing_id,
                status=Listing.Status.ACTIVE,
                moderation_status=Listing.ModerationStatus.APPROVED,
            )
        except Listing.DoesNotExist:
            raise NotFound("Bunday faol e'lon topilmadi.")

        favorite = Favorite.objects.filter(user=request.user, listing=listing).first()
        if favorite:
            favorite.delete()
            return Response(
                {
                    'is_favorited': False,
                    'message': "E'lon sevimlilar ro'yxatidan olib tashlandi.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            Favorite.objects.create(user=request.user, listing=listing)
            return Response(
                {
                    'is_favorited': True,
                    'message': "E'lon sevimlilar ro'yxatiga qo'shildi.",
                },
                status=status.HTTP_200_OK,
            )
