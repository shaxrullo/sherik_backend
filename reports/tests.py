from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, City
from listings.models import Listing
from reports.models import Report


class ReportsAPITests(TestCase):
    """Reports (Shikoyatlar) ilovasi testlari."""

    def setUp(self):
        self.client = APIClient()
        self.city = City.objects.create(name="Toshkent", slug="toshkent")

        self.author = User.objects.create_user(
            email="author@sherik.uz",
            password="StrongPassword123!",
            first_name="Muallif",
            city=self.city,
            is_verified=True,
        )
        self.reporter = User.objects.create_user(
            email="reporter@sherik.uz",
            password="StrongPassword123!",
            first_name="Shikoyatchi",
            city=self.city,
        )

        self.listing = Listing.objects.create(
            author=self.author,
            title="E'lon",
            description="Tavsif",
            city=self.city,
            price=1000000,
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )

        self.report_create_url = reverse('reports:create')
        self.my_reports_url = reverse('reports:my_reports')

    def test_anonymous_cannot_report(self):
        """Anonim foydalanuvchi shikoyat yubora olmasligi."""
        res = self.client.post(self.report_create_url, {
            'reported_listing_id': self.listing.id,
            'reason': "Soxta e'lon",
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_listing_success(self):
        """E'lon ustidan muvaffaqiyatli shikoyat yuborish."""
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(self.report_create_url, {
            'reported_listing_id': self.listing.id,
            'reason': "Rasmlar boshqa uyniki, aldamchilik",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Report.objects.filter(reporter=self.reporter, reported_listing=self.listing).exists())

    def test_cannot_report_own_listing(self):
        """Muallif o'zining e'loni ustidan shikoyat qila olmasligi."""
        self.client.force_authenticate(user=self.author)
        res = self.client.post(self.report_create_url, {
            'reported_listing_id': self.listing.id,
            'reason': "O'zimga shikoyat",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reported_listing_id', res.data)

    def test_cannot_report_without_target(self):
        """Hech qanday ob'ekt ko'rsatilmaganda xatolik berishi."""
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(self.report_create_url, {
            'reason': "Sabab bor, lekin kimga ekanligi yo'q",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_reports_list(self):
        """Foydalanuvchi o'z shikoyatlarini ko'rishi."""
        Report.objects.create(
            reporter=self.reporter,
            reported_listing=self.listing,
            reason="Shubhali ma'lumot",
        )
        self.client.force_authenticate(user=self.reporter)
        res = self.client.get(self.my_reports_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['reported_listing_id'], self.listing.id)
