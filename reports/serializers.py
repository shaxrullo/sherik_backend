from rest_framework import serializers
from .models import Report
from listings.models import Listing
from users.models import User


class ReportSerializer(serializers.ModelSerializer):
    """Shikoyat yaratish va ko'rish serializatori."""

    reported_listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        source='reported_listing',
        required=False,
        allow_null=True,
        error_messages={'does_not_exist': "Bunday e'lon topilmadi."}
    )
    reported_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='reported_user',
        required=False,
        allow_null=True,
        error_messages={'does_not_exist': "Bunday foydalanuvchi topilmadi."}
    )
    listing_title = serializers.CharField(source='reported_listing.title', read_only=True)
    user_email = serializers.CharField(source='reported_user.email', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'reported_listing_id',
            'listing_title',
            'reported_user_id',
            'user_email',
            'reason',
            'status',
            'moderator_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'moderator_notes', 'created_at', 'updated_at']
        extra_kwargs = {
            'reason': {'error_messages': {'blank': "Shikoyat sababi kiritilishi shart."}}
        }

    def validate(self, attrs):
        user = self.context['request'].user
        listing = attrs.get('reported_listing')
        target_user = attrs.get('reported_user')

        if not listing and not target_user:
            raise serializers.ValidationError(
                "Kamida bitta obyekt (e'lon yoki foydalanuvchi) ustidan shikoyat qilinishi kerak."
            )

        # O'z e'loniga shikoyat qila olmaslik
        if listing and listing.author == user:
            raise serializers.ValidationError({
                'reported_listing_id': "O'zingizning e'loningiz ustidan shikoyat qila olmaysiz."
            })

        # O'z ustidan shikoyat qila olmaslik
        if target_user and target_user == user:
            raise serializers.ValidationError({
                'reported_user_id': "O'zingizning ustingizdan shikoyat qila olmaysiz."
            })

        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)

