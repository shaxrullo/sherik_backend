from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, City, District, LifestylePreference
from listings.models import Listing


class MatchingAPITests(TestCase):
    """Matching (Moslik tavsiya tizimi) ilovasi testlari."""

    def setUp(self):
        self.client = APIClient()

        # Shaharlar va tumanlar
        self.toshkent = City.objects.create(name="Toshkent", slug="toshkent")
        self.samarqand = City.objects.create(name="Samarqand", slug="samarqand")
        self.yunusobod = District.objects.create(city=self.toshkent, name="Yunusobod")
        self.chilonzor = District.objects.create(city=self.toshkent, name="Chilonzor")

        # Qidiruvchi foydalanuvchi (Seeker, Toshkent, Yunusobod, Erkak, Chekmaydi, Juda toza)
        self.seeker = User.objects.create_user(
            email="seeker@sherik.uz",
            password="StrongPassword123!",
            first_name="Jasur",
            gender="male",
            city=self.toshkent,
            district=self.yunusobod,
            role="seeker",
        )
        self.seeker_lifestyle = LifestylePreference.objects.create(
            user=self.seeker,
            smoking="no",
            cleanliness="very_clean",
            pets="no",
            sleep_schedule="early_bird",
            guests="rarely",
        )

        # 1-muallif (Ideal moslik: Toshkent, Yunusobod, joy bor, erkaklar uchun, chekmaydi, juda toza)
        self.ideal_host = User.objects.create_user(
            email="ideal@sherik.uz",
            password="StrongPassword123!",
            first_name="Anvar",
            gender="male",
            city=self.toshkent,
            district=self.yunusobod,
            role="host",
            is_verified=True,
        )
        LifestylePreference.objects.create(
            user=self.ideal_host,
            smoking="no",
            cleanliness="very_clean",
            pets="no",
            sleep_schedule="early_bird",
            guests="rarely",
        )
        self.ideal_listing = Listing.objects.create(
            author=self.ideal_host,
            title="Ideal mos kvartira Yunusobodda",
            description="Tavsif",
            listing_type="have_room",
            city=self.toshkent,
            district=self.yunusobod,
            price=1500000,
            gender_preference="male",
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )

        # 2-muallif (Mos kelmaydigan: Samarqand, faqat ayollar, chekadi)
        self.bad_host = User.objects.create_user(
            email="bad@sherik.uz",
            password="StrongPassword123!",
            first_name="Zilola",
            gender="female",
            city=self.samarqand,
            role="host",
            is_verified=True,
        )
        LifestylePreference.objects.create(
            user=self.bad_host,
            smoking="yes",
            cleanliness="relaxed",
            pets="yes",
            sleep_schedule="night_owl",
            guests="welcome",
        )
        self.bad_listing = Listing.objects.create(
            author=self.bad_host,
            title="Samarqandda qizlar uchun joy",
            description="Tavsif",
            listing_type="have_room",
            city=self.samarqand,
            price=1000000,
            gender_preference="female",
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )

        self.recommendations_url = reverse('matching:recommendations')

    def test_anonymous_cannot_access_recommendations(self):
        """Anonim foydalanuvchi tavsiyalardan foydalana olmasligi."""
        res = self.client.get(self.recommendations_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recommendations_ranking_and_scores(self):
        """Mos e'lonlar to'g'ri tartibda (yuqori moslikdagi avval) chiqishi."""
        self.client.force_authenticate(user=self.seeker)
        res = self.client.get(self.recommendations_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 2)

        # Birinchi o'rindagi e'lon ideal_listing bo'lishi kerak
        top_match = results[0]
        self.assertEqual(top_match['listing']['id'], self.ideal_listing.id)
        self.assertGreater(top_match['match_score'], 80, "Ideal moslik 80% dan yuqori bo'lishi kerak")

        # Ikkinchi o'rindagi e'lon bad_listing bo'lishi va bali ancha past bo'lishi kerak
        second_match = results[1]
        self.assertEqual(second_match['listing']['id'], self.bad_listing.id)
        self.assertLess(second_match['match_score'], top_match['match_score'])

    def test_min_score_filter(self):
        """min_score parametri bilan past moslikdagi e'lonlarni chiqarib tashlash."""
        self.client.force_authenticate(user=self.seeker)
        res = self.client.get(f"{self.recommendations_url}?min_score=70")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['listing']['id'], self.ideal_listing.id)

    def test_own_listing_excluded_from_recommendations(self):
        """Foydalanuvchining o'z e'loni tavsiyalar ro'yxatida chiqmasligi."""
        Listing.objects.create(
            author=self.seeker,
            title="Seekerning o'z e'loni",
            description="Tavsif",
            city=self.toshkent,
            district=self.yunusobod,
            price=1200000,
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )
        self.client.force_authenticate(user=self.seeker)
        res = self.client.get(self.recommendations_url)
        results = res.data.get('results', res.data)
        listing_ids = [item['listing']['id'] for item in results]
        self.assertNotIn(self.seeker.listings.first().id, listing_ids)

    def test_listing_match_detail_view(self):
        """Aniq bitta e'lonning moslik tahlili tafsilotlarini olish."""
        self.client.force_authenticate(user=self.seeker)
        detail_url = reverse('matching:listing_match_detail', kwargs={'listing_id': self.ideal_listing.id})

        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['listing_id'], self.ideal_listing.id)
        self.assertIn('match_score', res.data)
        self.assertIn('match_breakdown', res.data)
        self.assertIn('match_details', res.data)
        self.assertGreater(res.data['match_score'], 80)
