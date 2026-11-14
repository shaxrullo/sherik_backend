from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import User, LifestylePreference, City


class UsersAuthAPITests(TestCase):
    """Foydalanuvchi va autentifikatsiya API testlari."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth:register')
        self.login_url = reverse('auth:login')
        self.token_refresh_url = reverse('auth:token_refresh')
        self.me_url = reverse('auth:me')
        self.lifestyle_url = reverse('auth:lifestyle')

        self.city_tashkent = City.objects.create(name='Toshkent')
        self.city_samarkand = City.objects.create(name='Samarqand')

        self.user_data = {
            'email': 'sherik@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'phone_number': '+998901234567',
            'gender': 'male',
            'city_id': self.city_tashkent.id,
            'birth_year': 2002,
            'role': 'seeker',
            'telegram_username': '@alivaliyev',
        }

    def test_user_registration_success(self):
        """Muvaffaqiyatli ro'yxatdan o'tish va JWT tokenlar olish."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], 'sherik@example.com')

        # Foydalanuvchi bazada mavjudligi va LifestylePreference yaratilganligi
        user = User.objects.get(email='sherik@example.com')
        self.assertTrue(user.check_password('StrongPassword123!'))
        self.assertTrue(hasattr(user, 'lifestyle'))
        self.assertEqual(user.city, self.city_tashkent)

    def test_registration_password_mismatch(self):
        """Parollar mos kelmaganda xatolik qaytarish."""
        data = self.user_data.copy()
        data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_registration_duplicate_email(self):
        """Mavjud email bilan qayta ro'yxatdan o'tishga yo'l qo'ymaslik."""
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_login_success(self):
        """Email va to'g'ri parol bilan tizimga kirish."""
        User.objects.create_user(
            email='sherik@example.com',
            password='StrongPassword123!',
            first_name='Ali',
        )
        response = self.client.post(self.login_url, {
            'email': 'sherik@example.com',
            'password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'sherik@example.com')

    def test_user_login_invalid_password(self):
        """Noto'g'ri parol kiritilganda xato xabari o'zbek tilida chiqishi."""
        User.objects.create_user(
            email='sherik@example.com',
            password='StrongPassword123!',
            first_name='Ali',
        )
        response = self.client.post(self.login_url, {
            'email': 'sherik@example.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Email yoki parol noto'g'ri", str(response.data))

    def test_token_refresh(self):
        """Refresh token orqali yangi access token olish."""
        user = User.objects.create_user(
            email='sherik@example.com',
            password='StrongPassword123!',
            first_name='Ali',
        )
        login_res = self.client.post(self.login_url, {
            'email': 'sherik@example.com',
            'password': 'StrongPassword123!',
        })
        refresh_token = login_res.data['refresh']

        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_profile_me_authenticated(self):
        """Kirgan foydalanuvchi o'z profilini ko'rishi va tahrirlashi."""
        user = User.objects.create_user(
            email='sherik@example.com',
            password='StrongPassword123!',
            first_name='Ali',
            phone_number='+998901234567',
            city=self.city_tashkent,
        )
        LifestylePreference.objects.create(user=user)
        self.client.force_authenticate(user=user)

        # GET /api/v1/auth/me/
        get_res = self.client.get(self.me_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['phone_number'], '+998901234567')
        self.assertEqual(get_res.data['city_name'], 'Toshkent')

        # PATCH /api/v1/auth/me/
        patch_res = self.client.patch(self.me_url, {
            'city_id': self.city_samarkand.id,
            'last_name': 'Karimov'
        })
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['city_name'], 'Samarqand')
        self.assertEqual(patch_res.data['last_name'], 'Karimov')

    def test_user_lifestyle_preference(self):
        """Foydalanuvchi turmush tarzi afzalliklarini ko'rish va yangilash."""
        user = User.objects.create_user(
            email='sherik@example.com',
            password='StrongPassword123!',
            first_name='Ali',
        )
        self.client.force_authenticate(user=user)

        response = self.client.patch(self.lifestyle_url, {
            'smoking': 'no',
            'cleanliness': 'very_clean',
            'curfew': '22:00 gacha',
            'pets': 'no',
            'guests': 'rarely',
            'sleep_schedule': 'early_bird',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cleanliness'], 'very_clean')
        self.assertEqual(response.data['sleep_schedule'], 'early_bird')

    def test_phone_number_visibility_rules(self):
        """
        Qoida: Telefon raqam boshqalarga faqat tizimga kirgan foydalanuvchiga ko'rinsin.
        Anonim foydalanuvchiga phone_number = None bo'lishi kerak.
        """
        user = User.objects.create_user(
            email='target@example.com',
            password='StrongPassword123!',
            first_name='Bobur',
            phone_number='+998939998877',
            city=self.city_tashkent,
        )
        LifestylePreference.objects.create(user=user)
        user_detail_url = reverse('users:user_detail', kwargs={'pk': user.pk})

        # 1. Anonim foydalanuvchi so'rovi (tizimga kirmagan)
        anon_res = self.client.get(user_detail_url)
        self.assertEqual(anon_res.status_code, status.HTTP_200_OK)
        self.assertIsNone(anon_res.data['phone_number'], "Anonim foydalanuvchiga telefon raqami ko'rinmasligi kerak!")

        # 2. Autentifikatsiyalangan boshqa foydalanuvchi so'rovi (tizimga kirgan)
        viewer = User.objects.create_user(
            email='viewer@example.com',
            password='StrongPassword123!',
            first_name='Sardor',
        )
        self.client.force_authenticate(user=viewer)
        auth_res = self.client.get(user_detail_url)
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            auth_res.data['phone_number'],
            '+998939998877',
            "Tizimga kirgan foydalanuvchiga telefon raqami ko'rinishi shart!"
        )

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_success(self, mock_verify):
        """Google OAuth ID token orqali login/ro'yxatdan o'tish."""
        mock_verify.return_value = {
            'email': 'googleuser@gmail.com',
            'name': 'Google User',
            'given_name': 'Google',
            'family_name': 'User',
            'sub': '1234567890',
        }
        google_url = reverse('auth:google_auth')
        response = self.client.post(google_url, {'token': 'fake-valid-google-id-token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'googleuser@gmail.com')
        self.assertTrue(User.objects.filter(email='googleuser@gmail.com').exists())
