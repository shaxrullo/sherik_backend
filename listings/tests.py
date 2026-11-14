import io
from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, City, District
from listings.models import Listing, ListingPhoto


def create_test_image(name="test.jpg"):
    file_obj = io.BytesIO()
    image = Image.new("RGBA", size=(100, 100), color=(256, 0, 0))
    image.save(file_obj, "png")
    file_obj.seek(0)
    return SimpleUploadedFile(name, file_obj.read(), content_type="image/png")


class ListingAPITests(TestCase):
    """E'lonlar ilovasi API testlari."""

    def setUp(self):
        self.client = APIClient()

        # Shaharlar va tumanlar
        self.toshkent = City.objects.create(name="Toshkent", slug="toshkent")
        self.samarqand = City.objects.create(name="Samarqand", slug="samarqand")
        self.yunusobod = District.objects.create(city=self.toshkent, name="Yunusobod")
        self.chilonzor = District.objects.create(city=self.toshkent, name="Chilonzor")
        self.samarqand_tuman = District.objects.create(city=self.samarqand, name="Bog'ishamol")

        # Foydalanuvchilar
        self.user1 = User.objects.create_user(
            email="user1@sherik.uz",
            password="StrongPassword123!",
            first_name="Ali",
            phone_number="+998901112233",
            city=self.toshkent,
            is_verified=False,
        )
        self.user2 = User.objects.create_user(
            email="user2@sherik.uz",
            password="StrongPassword123!",
            first_name="Vali",
            phone_number="+998902223344",
            city=self.toshkent,
            is_verified=True,  # Ishonchli
        )

        self.list_create_url = reverse('listings:list_create')
        self.my_listings_url = reverse('listings:my_listings')

    def test_listing_creation_unverified_user_pending(self):
        """Oddiy foydalanuvchi yaratgan e'lon pending holatida bo'lishi."""
        self.client.force_authenticate(user=self.user1)
        data = {
            'title': "Chilonzorda sheriklikka joy bor",
            'description': "Metro yaqinida, barcha qulayliklar bor",
            'listing_type': 'have_room',
            'city_id': self.toshkent.id,
            'district_id': self.chilonzor.id,
            'address_line': "19-kvartal, 12-uy",
            'price': 1200000,
            'capacity': 2,
            'gender_preference': 'male',
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['moderation_status'], Listing.ModerationStatus.PENDING)

        listing = Listing.objects.get(id=res.data['id'])
        self.assertEqual(listing.author, self.user1)

    def test_listing_creation_verified_user_auto_approved(self):
        """Ishonchli (is_verified=True) foydalanuvchi e'loni avtomatik approved bo'lishi."""
        self.client.force_authenticate(user=self.user2)
        data = {
            'title': "Yunusobodda toza kvartira",
            'description': "Talabalar uchun",
            'listing_type': 'have_room',
            'city_id': self.toshkent.id,
            'district_id': self.yunusobod.id,
            'price': 1500000,
            'capacity': 1,
            'gender_preference': 'any',
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['moderation_status'], Listing.ModerationStatus.APPROVED)

    def test_district_city_mismatch_validation(self):
        """Tuman boshqa shaharga tegishli bo'lsa xatolik berishi."""
        self.client.force_authenticate(user=self.user1)
        data = {
            'title': "Xato tuman testi",
            'description': "Tavsif",
            'city_id': self.toshkent.id,
            'district_id': self.samarqand_tuman.id,  # Samarqand tumani Toshkent bilan tanlangan
            'price': 1000000,
        }
        res = self.client.post(self.list_create_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('district_id', res.data)

    def test_public_listing_list_only_approved(self):
        """Ommaviy ro'yxatda faqat approved va active e'lonlar ko'rinishi."""
        # 1 ta approved e'lon
        Listing.objects.create(
            author=self.user2,
            title="Tasdiqlangan e'lon",
            description="Tavsif",
            city=self.toshkent,
            price=1500000,
            moderation_status=Listing.ModerationStatus.APPROVED,
            status=Listing.Status.ACTIVE,
        )
        # 1 ta pending e'lon
        Listing.objects.create(
            author=self.user1,
            title="Kutilayotgan e'lon",
            description="Tavsif",
            city=self.toshkent,
            price=1200000,
            moderation_status=Listing.ModerationStatus.PENDING,
            status=Listing.Status.ACTIVE,
        )

        res = self.client.get(self.list_create_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Paginatsiya natijasi
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Tasdiqlangan e'lon")

    def test_phone_number_visibility_in_listing(self):
        """
        Qoida: E'lon muallifining telefon raqami anonimga null,
        tizimga kirgan foydalanuvchiga esa ko'rinishi kerak.
        """
        listing = Listing.objects.create(
            author=self.user2,
            title="Telefon ko'rinishi testi",
            description="Tavsif",
            city=self.toshkent,
            price=1500000,
            moderation_status=Listing.ModerationStatus.APPROVED,
            status=Listing.Status.ACTIVE,
        )
        detail_url = reverse('listings:detail', kwargs={'pk': listing.pk})

        # 1. Anonim foydalanuvchi
        anon_res = self.client.get(detail_url)
        self.assertEqual(anon_res.status_code, status.HTTP_200_OK)
        self.assertIsNone(anon_res.data['author']['phone_number'])

        # 2. Tizimga kirgan foydalanuvchi
        self.client.force_authenticate(user=self.user1)
        auth_res = self.client.get(detail_url)
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_res.data['author']['phone_number'], self.user2.phone_number)

    def test_permission_only_owner_can_edit_or_delete(self):
        """Faqat e'lon egasi o'z e'lonini tahrirlashi va o'chira olishi."""
        listing = Listing.objects.create(
            author=self.user1,
            title="Ali e'loni",
            description="Tavsif",
            city=self.toshkent,
            price=1000000,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )
        detail_url = reverse('listings:detail', kwargs={'pk': listing.pk})

        # Boshqa foydalanuvchi (user2) tahrirlamoqchi bo'ladi -> 403 Forbidden
        self.client.force_authenticate(user=self.user2)
        patch_res = self.client.patch(detail_url, {'price': 2000000})
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)

        # O'chirmoqchi bo'ladi -> 403 Forbidden
        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

        # O'z egasi (user1) tahrirlaydi -> 200 OK
        self.client.force_authenticate(user=self.user1)
        owner_patch = self.client.patch(detail_url, {'price': 1300000})
        self.assertEqual(owner_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_patch.data['price'], '1300000')

        # O'z egasi o'chiradi -> 204 No Content
        owner_del = self.client.delete(detail_url)
        self.assertEqual(owner_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Listing.objects.filter(id=listing.id).exists())

    def test_my_listings_endpoint(self):
        """Mening e'lonlarim endpointida o'zining pending e'lonlari ham chiqishi."""
        Listing.objects.create(
            author=self.user1,
            title="Pending e'lonim",
            description="Tavsif",
            city=self.toshkent,
            price=1000000,
            moderation_status=Listing.ModerationStatus.PENDING,
        )
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(self.my_listings_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['moderation_status'], Listing.ModerationStatus.PENDING)

    def test_filters_price_and_city(self):
        """E'lonlarni shahar va narx oralig'i bo'yicha filtrlash."""
        Listing.objects.create(
            author=self.user2,
            title="Arzon Toshkent",
            description="Tavsif",
            city=self.toshkent,
            price=1000000,
            listing_type='have_room',
            gender_preference='male',
            moderation_status=Listing.ModerationStatus.APPROVED,
        )
        Listing.objects.create(
            author=self.user2,
            title="Qimmat Toshkent",
            description="Tavsif",
            city=self.toshkent,
            price=3000000,
            listing_type='have_room',
            gender_preference='male',
            moderation_status=Listing.ModerationStatus.APPROVED,
        )
        Listing.objects.create(
            author=self.user2,
            title="Samarqand e'loni",
            description="Tavsif",
            city=self.samarqand,
            price=1500000,
            listing_type='have_room',
            gender_preference='female',
            moderation_status=Listing.ModerationStatus.APPROVED,
        )

        # 1. Faqat Toshkent (city_slug=toshkent)
        res_city = self.client.get(f"{self.list_create_url}?city_slug=toshkent")
        self.assertEqual(len(res_city.data['results']), 2)

        # 2. Narx oralig'i (min_price=1200000, max_price=2000000)
        res_price = self.client.get(f"{self.list_create_url}?min_price=1200000&max_price=2000000")
        self.assertEqual(len(res_price.data['results']), 1)
        self.assertEqual(res_price.data['results'][0]['title'], "Samarqand e'loni")

        # 3. Jins bo'yicha talab (gender_preference=female)
        res_gender = self.client.get(f"{self.list_create_url}?gender_preference=female")
        self.assertEqual(len(res_gender.data['results']), 1)

    def test_photo_upload_and_delete(self):
        """E'longa rasm yuklash va o'chirish."""
        listing = Listing.objects.create(
            author=self.user1,
            title="Rasmli e'lon",
            description="Tavsif",
            city=self.toshkent,
            price=1000000,
            moderation_status=Listing.ModerationStatus.APPROVED,
        )
        upload_url = reverse('listings:photo_upload', kwargs={'listing_id': listing.id})

        # Boshqa foydalanuvchi rasm yuklamoqchi bo'lsa -> 403 Forbidden
        self.client.force_authenticate(user=self.user2)
        test_img = create_test_image()
        res_forbidden = self.client.post(upload_url, {'image': test_img, 'is_main': True}, format='multipart')
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # E'lon egasi rasm yuklaydi -> 201 Created
        self.client.force_authenticate(user=self.user1)
        test_img = create_test_image()
        res_upload = self.client.post(upload_url, {'image': test_img, 'is_main': True}, format='multipart')
        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        photo_id = res_upload.data['id']
        self.assertTrue(ListingPhoto.objects.filter(id=photo_id).exists())

        # Rasmni o'chirish
        delete_url = reverse('listings:photo_delete', kwargs={'pk': photo_id})
        res_del = self.client.delete(delete_url)
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ListingPhoto.objects.filter(id=photo_id).exists())
