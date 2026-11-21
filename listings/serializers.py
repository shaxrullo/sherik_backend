from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Listing, ListingPhoto
from users.models import City, District, User


class ListingPhotoSerializer(serializers.ModelSerializer):
    """E'lon rasmlari serializatori."""

    class Meta:
        model = ListingPhoto
        fields = ['id', 'image', 'is_main', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class AuthorPublicSerializer(serializers.ModelSerializer):
    """
    E'lon muallifining ommaviy ma'lumotlari.
    Qoida: Telefon raqam faqat tizimga kirgan foydalanuvchiga ko'rinadi.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'avatar',
            'telegram_username',
            'is_verified',
            'date_joined',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # Agar so'rov yuborgan foydalanuvchi anonim bo'lsa, telefon raqami ko'rinmaydi
        if not request or not request.user or not request.user.is_authenticated:
            data['phone_number'] = None
        return data


class ListingListSerializer(serializers.ModelSerializer):
    """E'lonlar ro'yxati (ixcham) serializatori."""

    author = AuthorPublicSerializer(read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    photos = ListingPhotoSerializer(many=True, read_only=True)
    main_photo = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'listing_type',
            'price',
            'currency',
            'capacity',
            'total_residents',
            'gender_preference',
            'amenities',
            'near_subway',
            'nearby_universities',
            'status',
            'moderation_status',
            'rejection_reason',
            'city_name',
            'district_name',
            'main_photo',
            'photos',
            'author',
            'created_at',
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_main_photo(self, obj):
        # Asosiy rasm yoki birinchi rasmni olish
        photos = list(obj.photos.all())
        if not photos:
            return None
        main = next((p for p in photos if p.is_main), photos[0])
        request = self.context.get('request')
        if request and main.image:
            return request.build_absolute_uri(main.image.url)
        return main.image.url if main.image else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # Agar so'rov yuboruvchi e'lon muallifi yoki staff bo'lmasa, moderatsiya tafsilotlari yashiriladi
        is_owner_or_staff = (
            request
            and request.user.is_authenticated
            and (request.user == instance.author or request.user.is_staff)
        )
        if not is_owner_or_staff:
            data.pop('rejection_reason', None)
        return data


class ListingDetailSerializer(serializers.ModelSerializer):
    """Bitta e'lonning to'liq ma'lumotlari serializatori."""

    author = AuthorPublicSerializer(read_only=True)
    city_id = serializers.IntegerField(source='city.id', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_id = serializers.IntegerField(source='district.id', read_only=True, allow_null=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    photos = ListingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'description',
            'listing_type',
            'city_id',
            'city_name',
            'district_id',
            'district_name',
            'address_line',
            'price',
            'currency',
            'capacity',
            'total_residents',
            'gender_preference',
            'amenities',
            'near_subway',
            'nearby_universities',
            'status',
            'moderation_status',
            'rejection_reason',
            'photos',
            'author',
            'created_at',
            'updated_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        is_owner_or_staff = (
            request
            and request.user.is_authenticated
            and (request.user == instance.author or request.user.is_staff)
        )
        # Faqat e'lon egasi va admin/moderator rad etish sababini ko'ra oladi
        if not is_owner_or_staff:
            data.pop('rejection_reason', None)

        data['is_favorited'] = False
        if request and request.user and request.user.is_authenticated:
            data['is_favorited'] = instance.favorited_by.filter(user=request.user).exists()

        return data


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    """E'lon yaratish va yangilash serializatori."""

    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_active=True),
        source='city',
        error_messages={'does_not_exist': "Bunday shahar topilmadi yoki u nofaol."}
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.filter(is_active=True),
        source='district',
        required=False,
        allow_null=True,
        error_messages={'does_not_exist': "Bunday tuman topilmadi yoki u nofaol."}
    )

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'description',
            'listing_type',
            'city_id',
            'district_id',
            'address_line',
            'price',
            'currency',
            'capacity',
            'total_residents',
            'gender_preference',
            'amenities',
            'near_subway',
            'nearby_universities',
            'status',
            'moderation_status',
            'rejection_reason',
        ]
        read_only_fields = ['id', 'moderation_status', 'rejection_reason']
        extra_kwargs = {
            'title': {'error_messages': {'blank': "Sarlavha kiritilishi shart."}},
            'description': {'error_messages': {'blank': "Tavsif kiritilishi shart."}},
            'price': {'error_messages': {'invalid': "Narx noto'g'ri kiritildi."}},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Oylik narx 0 dan katta bo'lishi kerak.")
        return value

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError("Joylar soni kamida 1 bo'lishi kerak.")
        return value

    def validate(self, attrs):
        city = attrs.get('city') or (self.instance.city if self.instance else None)
        district = attrs.get('district') or (self.instance.district if self.instance else None)

        if district and city and district.city != city:
            raise serializers.ValidationError({
                'district_id': f"Tanlangan tuman ({district.name}) tanlangan shaharga ({city.name}) tegishli emas."
            })
        return attrs

    def create(self, validated_data):
        from django.utils import timezone
        user = self.context['request'].user
        validated_data['author'] = user
        if getattr(user, 'is_verified', False) or getattr(user, 'is_staff', False):
            validated_data['moderation_status'] = Listing.ModerationStatus.APPROVED
            validated_data['moderated_at'] = timezone.now()
        return super().create(validated_data)


class ListingPhotoUploadSerializer(serializers.ModelSerializer):
    """E'longa rasm yuklash serializatori."""

    class Meta:
        model = ListingPhoto
        fields = ['id', 'image', 'is_main', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {
            'image': {'error_messages': {'required': "Rasm fayli yuklanishi shart."}}
        }
