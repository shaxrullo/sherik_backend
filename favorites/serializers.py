from rest_framework import serializers
from .models import Favorite
from listings.models import Listing
from listings.serializers import ListingListSerializer


class FavoriteListSerializer(serializers.ModelSerializer):
    """Sevimli e'lonlar ro'yxati serializatori."""

    listing = ListingListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'listing', 'created_at']


class FavoriteActionSerializer(serializers.Serializer):
    """Sevimlilarga qo'shish / olib tashlash serializatori."""

    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.filter(
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        ),
        source='listing',
        error_messages={'does_not_exist': "Bunday faol e'lon topilmadi."}
    )

    def validate(self, attrs):
        user = self.context['request'].user
        listing = attrs['listing']
        # Validatsiyada kerak bo'lsa qo'shimcha tekshiruvlar
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        listing = validated_data['listing']

        favorite, created = Favorite.objects.get_or_create(user=user, listing=listing)
        return {
            'favorite_id': favorite.id,
            'listing_id': listing.id,
            'is_favorited': True,
            'created': created,
        }

