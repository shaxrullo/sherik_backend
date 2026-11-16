from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import User, LifestylePreference, City, District


class DistrictSerializer(serializers.ModelSerializer):
    """Tuman ma'lumotnomasi serializatori."""

    class Meta:
        model = District
        fields = ['id', 'name', 'city']


class CitySerializer(serializers.ModelSerializer):
    """Shahar ma'lumotnomasi serializatori."""
    districts = DistrictSerializer(many=True, read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'slug', 'districts']


class LifestylePreferenceSerializer(serializers.ModelSerializer):
    """Turmush tarzi afzalliklari serializatori."""

    class Meta:
        model = LifestylePreference
        fields = [
            'id',
            'smoking',
            'cleanliness',
            'curfew',
            'pets',
            'guests',
            'sleep_schedule',
            'notes',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Foydalanuvchini ro'yxatdan o'tkazish serializatori."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'min_length': "Parol kamida 8 ta belgidan iborat bo'lishi kerak.",
            'blank': "Parol kiritilishi shart.",
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        error_messages={'blank': "Parolni tasdiqlash kiritilishi shart."}
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_active=True),
        source='city',
        required=False,
        allow_null=True,
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.filter(is_active=True),
        source='district',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone_number',
            'gender',
            'city_id',
            'district_id',
            'birth_year',
            'role',
            'telegram_username',
        ]
        extra_kwargs = {
            'email': {
                'error_messages': {
                    'required': "Email kiritilishi shart.",
                    'invalid': "Email formati noto'g'ri.",
                }
            },
            'first_name': {
                'error_messages': {
                    'required': "Ism kiritilishi shart.",
                    'blank': "Ism bo'sh bo'lishi mumkin emas.",
                }
            }
        }

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Ushbu email manzili allaqachon ro'yxatdan o'tgan.")
        return email

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': "Kiritilgan parollar bir-biriga mos kelmadi."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        # Avtomatik lifestyle profile yaratish
        LifestylePreference.objects.get_or_create(user=user)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token olish uchun email va parol serializatori."""

    default_error_messages = {
        'no_active_account': "Email yoki parol noto'g'ri kiritildi.",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        # Agar foydalanuvchi bloklangan bo'lsa (is_active=False), Django o'zi ruxsat bermaydi
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_phone_verified': self.user.is_phone_verified,
            'is_verified': self.user.is_verified,
        }
        return data


class GoogleAuthSerializer(serializers.Serializer):
    """Google ID Token orqali kirish/ro'yxatdan o'tish serializatori."""

    token = serializers.CharField(
        required=True,
        error_messages={'blank': "Google tokeni kiritilishi shart."}
    )

    def validate_token(self, token):
        try:
            client_id = settings.GOOGLE_CLIENT_ID or None
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                audience=client_id,
            )
            return idinfo
        except Exception as e:
            raise serializers.ValidationError(
                f"Google token yaroqsiz yoki muddati o'tgan: {str(e)}"
            )

    def save(self):
        idinfo = self.validated_data['token']
        email = idinfo.get('email', '').lower().strip()
        if not email:
            raise serializers.ValidationError({"email": "Google hisobida email topilmadi."})

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': idinfo.get('given_name') or idinfo.get('name', 'Foydalanuvchi'),
                'last_name': idinfo.get('family_name', ''),
            }
        )

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Sizning hisobingiz bloklangan."})

        if created:
            LifestylePreference.objects.get_or_create(user=user)

        refresh = RefreshToken.for_user(user)
        return {
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_phone_verified': user.is_phone_verified,
                'is_verified': user.is_verified,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'created': created,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Foydalanuvchining shaxsiy profili (o'zi uchun to'liq ma'lumot)."""

    lifestyle = LifestylePreferenceSerializer(read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(is_active=True),
        source='city',
        required=False,
        allow_null=True,
    )
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.filter(is_active=True),
        source='district',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'is_phone_verified',
            'is_verified',
            'gender',
            'city_id',
            'city_name',
            'district_id',
            'district_name',
            'birth_year',
            'role',
            'is_staff',
            'is_superuser',
            'telegram_username',
            'avatar',
            'bio',
            'lifestyle',
            'date_joined',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_phone_verified',
            'is_verified',
            'is_staff',
            'is_superuser',
            'date_joined',
            'updated_at',
        ]


class PublicUserListingSerializer(serializers.Serializer):
    """Foydalanuvchi profilida ko'rsatiladigan e'lon (ixcham)."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    listing_type = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    city_name = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    main_photo = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None

    def get_district_name(self, obj):
        return obj.district.name if obj.district else None

    def get_main_photo(self, obj):
        photos = list(obj.photos.all())
        if not photos:
            return None
        main = next((p for p in photos if p.is_main), photos[0])
        request = self.context.get('request')
        if request and main.image:
            return request.build_absolute_uri(main.image.url)
        return main.image.url if main.image else None


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Boshqa foydalanuvchilarning ommaviy profili.
    Qoida: Telefon raqam faqat tizimga kirgan foydalanuvchiga ko'rinadi.
    listings - foydalanuvchining faol va tasdiqlangan e'lonlari.
    """

    lifestyle = LifestylePreferenceSerializer(read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    listings = serializers.SerializerMethodField()
    listings_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'is_phone_verified',
            'is_verified',
            'gender',
            'city_name',
            'district_name',
            'birth_year',
            'role',
            'telegram_username',
            'avatar',
            'bio',
            'lifestyle',
            'date_joined',
            'listings',
            'listings_count',
        ]

    def get_listings(self, instance):
        from listings.models import Listing
        qs = (
            Listing.objects
            .filter(
                author=instance,
                status=Listing.Status.ACTIVE,
                moderation_status=Listing.ModerationStatus.APPROVED,
            )
            .select_related('city', 'district')
            .prefetch_related('photos')
            .order_by('-created_at')
        )
        return PublicUserListingSerializer(qs, many=True, context=self.context).data

    def get_listings_count(self, instance):
        from listings.models import Listing
        return Listing.objects.filter(
            author=instance,
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        ).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # Agar so'rov yuborgan foydalanuvchi tizimga kirmagan bo'lsa, telefon raqam yashiriladi
        if not request or not request.user or not request.user.is_authenticated:
            data['phone_number'] = None
        return data
