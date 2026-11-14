from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, LifestylePreference
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    GoogleAuthSerializer,
    UserProfileSerializer,
    PublicUserSerializer,
    LifestylePreferenceSerializer,
)


@extend_schema(
    tags=['Auth'],
    summary="Yangi foydalanuvchini ro'yxatdan o'tkazish",
    description="Email va parol orqali yangi hisob yaratadi va JWT tokenlarini qaytaradi.",
    responses={
        201: OpenApiResponse(description="Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi"),
        400: OpenApiResponse(description="Validatsiya xatosi"),
    }
)
class RegisterView(generics.CreateAPIView):
    """Foydalanuvchini ro'yxatdan o'tkazish viewsi."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Yangi ro'yxatdan o'tgan foydalanuvchiga to'g'ridan-to'g'ri JWT token berish
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': "Ro'yxatdan muvaffaqiyatli o'tdingiz.",
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['Auth'],
    summary="Tizimga kirish (JWT token olish)",
    description="Email va parol orqali tizimga kirish.",
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Email va parol orqali login qilish viewsi."""

    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Auth'],
    summary="Google orqali tizimga kirish / ro'yxatdan o'tish",
    description="Google OAuth2 ID tokenini yuborib JWT access va refresh tokenlarini olish.",
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(description="Tizimga muvaffaqiyatli kirildi"),
        400: OpenApiResponse(description="Google token xatosi"),
    }
)
class GoogleAuthView(APIView):
    """Google ID Token orqali autentifikatsiya viewsi."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Auth'],
    summary="Shaxsiy profilni ko'rish va tahrirlash",
    description="Avtorizatsiyadan o'tgan foydalanuvchining shaxsiy ma'lumotlarini olish va yangilash.",
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Kirgan foydalanuvchining o'z profili."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return User.objects.select_related('lifestyle').get(pk=self.request.user.pk)


@extend_schema(
    tags=['Auth'],
    summary="Shaxsiy turmush tarzi afzalliklarini ko'rish va tahrirlash",
    description="Foydalanuvchi turmush tarzi parametrlari (chekish, tozalik, hayvonlar, uyqu rejimi).",
)
class UserLifestylePreferenceView(generics.RetrieveUpdateAPIView):
    """Foydalanuvchining turmush tarzi afzalliklari viewsi."""

    serializer_class = LifestylePreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        lifestyle, _ = LifestylePreference.objects.get_or_create(user=self.request.user)
        return lifestyle


@extend_schema(
    tags=['Users'],
    summary="Boshqa foydalanuvchining ommaviy profili",
    description="Foydalanuvchining ommaviy ma'lumotlari. Telefon raqami faqat tizimga kirganlarga ko'rinadi.",
)
class PublicUserDetailView(generics.RetrieveAPIView):
    """Boshqa foydalanuvchining profilini ko'rish."""

    queryset = User.objects.filter(is_active=True).select_related('lifestyle')
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
