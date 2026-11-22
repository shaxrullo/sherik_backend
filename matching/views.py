from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from listings.models import Listing
from listings.pagination import StandardResultsSetPagination
from matching.services_cached import CachedMatchingService
from .serializers import MatchedListingSerializer, ListingMatchDetailSerializer


@extend_schema(
    tags=['Matching'],
    summary="Senga mos e'lonlar (Tavsiya tizimi)",
    description=(
        "Foydalanuvchining hududi, jinsi, roli va turmush tarzi afzalliklari (Lifestyle) "
        "asosida moslik balli (0-100%) hisoblanadi va eng yuqori mos e'lonlar tartibida qaytariladi."
    ),
    parameters=[
        OpenApiParameter(
            name='min_score',
            type=int,
            description="Minimal moslik bali (masalan, 50)",
            required=False,
        ),
        OpenApiParameter(
            name='page',
            type=int,
            description="Sahifa raqami",
            required=False,
        ),
        OpenApiParameter(
            name='page_size',
            type=int,
            description="Sahifadagi natijalar soni",
            required=False,
        ),
        OpenApiParameter(
            name='refresh',
            type=bool,
            description="Cache'ni bypass qilib yangi hisoblash (default: false)",
            required=False,
        ),
    ],
    responses={
        200: MatchedListingSerializer(many=True),
        401: OpenApiResponse(description="Avtorizatsiyadan o'tilmagan"),
    }
)
class MatchingRecommendationsView(APIView):
    """Foydalanuvchiga mos e'lonlarni tavsiya qilish viewsi (cached)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        min_score = int(request.query_params.get('min_score', 0))
        force_refresh = request.query_params.get('refresh', '').lower() == 'true'
        
        # Get cached recommendations
        recommended_data = CachedMatchingService.get_recommendations_for_user(
            user,
            limit=100,  # Get top 100, then filter by min_score
            force_refresh=force_refresh
        )
        
        # Filter by minimum score
        matched_results = [
            {
                'listing': item['listing'],
                'match_score': item['score']['total_score'],
                'match_breakdown': item['score']['breakdown'],
                'match_details': item['score']['details'],
            }
            for item in recommended_data
            if item['score']['total_score'] >= min_score
        ]
        
        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(matched_results, request, view=self)

        serializer = MatchedListingSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@extend_schema(
    tags=['Matching'],
    summary="Bitta e'lon bilan moslik tahlili",
    description="Aniq bir e'lonning joriy foydalanuvchiga moslik foizini va sabablarini qaytaradi.",
    parameters=[
        OpenApiParameter(
            name='refresh',
            type=bool,
            description="Cache'ni bypass qilib yangi hisoblash (default: false)",
            required=False,
        ),
    ],
    responses={
        200: ListingMatchDetailSerializer,
        404: OpenApiResponse(description="E'lon topilmadi"),
    }
)
class ListingMatchCheckView(APIView):
    """Aniq bitta e'lon bilan moslikni tekshirish viewsi (cached)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, listing_id):
        try:
            listing = (
                Listing.objects.select_related('author', 'author__lifestyle', 'city', 'district')
                .get(
                    id=listing_id,
                    status=Listing.Status.ACTIVE,
                    moderation_status=Listing.ModerationStatus.APPROVED,
                )
            )
        except Listing.DoesNotExist:
            raise NotFound("Bunday faol e'lon topilmadi.")

        force_refresh = request.query_params.get('refresh', '').lower() == 'true'
        match_data = CachedMatchingService.get_match_score(
            request.user,
            listing,
            force_refresh=force_refresh
        )
        
        response_data = {
            'listing_id': listing.id,
            'listing_title': listing.title,
            'match_score': match_data['total_score'],
            'match_breakdown': match_data['breakdown'],
            'match_details': match_data['details'],
        }
        return Response(response_data, status=status.HTTP_200_OK)
