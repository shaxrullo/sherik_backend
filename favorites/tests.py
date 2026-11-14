from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, City
from listings.models import Listing
from favorites.models import Favorite


class FavoritesAPITests(TestCase):
    """Favorites (Sevimlilar) ilovasi testlari."""

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
        self.user = User.objects.create_user(
            email="user@sherik.uz",
            password="StrongPassword123!",
            first_name="Foydalanuvchi",
            city=self.city,
        )

        self.listing = Listing.objects.create(
            author=self.author,
            title="Shinam kvartira",
            description="Tavsif",
            city=self.city,
            price=1500000,
            status=Listing.Status.ACTIVE,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )

        self.fav_list_url = reverse('favorites:list')
        self.fav_add_url = reverse('favorites:add')
        self.fav_toggle_url = reverse('favorites:toggle')

    def test_anonymous_cannot_access_favorites(self):
        """Anonim foydalanuvchi sevimlilardan foydalana olmasligi."""
        res = self.client.get(self.fav_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_favorite_success(self):
        """E'lonni sevimlilarga qo'shish."""
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.fav_add_url, {'listing_id': self.listing.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Favorite.objects.filter(user=self.user, listing=self.listing).exists())

    def test_get_favorite_list(self):
        """Foydalanuvchining sevimli e'lonlarini ro'yxatda olish."""
        Favorite.objects.create(user=self.user, listing=self.listing)

        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.fav_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['listing']['id'], self.listing.id)

    def test_remove_favorite(self):
        """Sevimlilardan e'lonni olib tashlash."""
        Favorite.objects.create(user=self.user, listing=self.listing)

        self.client.force_authenticate(user=self.user)
        del_url = reverse('favorites:remove', kwargs={'listing_id': self.listing.id})
        res = self.client.delete(del_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(user=self.user, listing=self.listing).exists())

    def test_toggle_favorite(self):
        """Toggle orqali e'lonni sevimlilarga qo'shish va qayta bosganda olib tashlash."""
        self.client.force_authenticate(user=self.user)

        # 1-marta toggle: qo'shiladi
        res1 = self.client.post(self.fav_toggle_url, {'listing_id': self.listing.id})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['is_favorited'])
        self.assertTrue(Favorite.objects.filter(user=self.user, listing=self.listing).exists())

        # 2-marta toggle: olib tashlanadi
        res2 = self.client.post(self.fav_toggle_url, {'listing_id': self.listing.id})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['is_favorited'])
        self.assertFalse(Favorite.objects.filter(user=self.user, listing=self.listing).exists())
