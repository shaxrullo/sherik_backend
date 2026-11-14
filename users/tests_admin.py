from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User, City, District, AdminActionLog
from listings.models import Listing, ListingPhoto
from reports.models import Report
from users.services import log_admin_action


class AdminAndModerationTests(TestCase):
    """Admin paneli, moderatsiya, rollar va xavfsizlik testlari."""

    def setUp(self):
        self.client = APIClient()

        # Shahar va tuman
        self.city = City.objects.create(name="Toshkent", slug="toshkent")
        self.district = District.objects.create(city=self.city, name="Yunusobod")

        # Oddiy foydalanuvchi
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            password="StrongPassword123!",
            first_name="Oddiy",
            city=self.city,
            district=self.district,
            is_verified=False,
        )

        # Tasdiqlangan ishonchli foydalanuvchi
        self.verified_user = User.objects.create_user(
            email="verified@example.com",
            password="StrongPassword123!",
            first_name="Ishonchli",
            city=self.city,
            district=self.district,
            is_verified=True,
        )

        # Superadmin
        self.superadmin = User.objects.create_superuser(
            email="superadmin@sherik.uz",
            password="SuperPassword123!",
            first_name="SuperAdmin",
        )

        # Moderator
        from django.core.management import call_command
        call_command('setup_roles')
        self.moderator_group = Group.objects.get(name='Moderator')

        self.moderator = User.objects.create_user(
            email="moderator@sherik.uz",
            password="ModeratorPass123!",
            first_name="ModeratorAli",
            is_staff=True,
        )
        self.moderator.groups.add(self.moderator_group)

    def test_listing_moderation_flow_unverified_user(self):
        """Oddiy (is_verified=False) foydalanuvchi e'loni avtomatik pending holatida bo'lishi."""
        listing = Listing.objects.create(
            author=self.regular_user,
            title="Ijara xona bor",
            description="2 kishilik xona",
            city=self.city,
            district=self.district,
            price=1500000,
        )
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.PENDING)
        self.assertIsNone(listing.moderated_at)

    def test_listing_auto_approval_for_verified_user(self):
        """Tasdiqlangan ishonchli (is_verified=True) foydalanuvchi e'loni avtomatik approved bo'lishi."""
        listing = Listing.objects.create(
            author=self.verified_user,
            title="Yangi uyga sherik",
            description="Barcha sharoitlar bor",
            city=self.city,
            district=self.district,
            price=2000000,
        )
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.APPROVED)
        self.assertIsNotNone(listing.moderated_at)

    def test_moderator_action_approve_and_reject(self):
        """Moderator e'lonni tasdiqlashi va rad etishi hamda audit log yozilishi."""
        listing = Listing.objects.create(
            author=self.regular_user,
            title="Ko'rib chiqilishi kerak bo'lgan e'lon",
            description="Tavsif",
            city=self.city,
            district=self.district,
            price=1000000,
        )
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.PENDING)

        # Tasdiqlash
        listing.moderation_status = Listing.ModerationStatus.APPROVED
        listing.moderated_by = self.moderator
        listing.moderated_at = timezone.now()
        listing.save()
        log_admin_action(self.moderator, "APPROVE_LISTING", listing, "Tasdiqlandi")

        listing.refresh_from_db()
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.APPROVED)
        self.assertEqual(listing.moderated_by, self.moderator)

        # Audit log tekshirish
        log_entry = AdminActionLog.objects.filter(target_id=listing.id, action="APPROVE_LISTING").first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.user, self.moderator)

        # Rad etish
        listing.moderation_status = Listing.ModerationStatus.REJECTED
        listing.rejection_reason = "Noto'g'ri narx va manzil"
        listing.save()
        log_admin_action(self.moderator, "REJECT_LISTING", listing, "Rad etildi")

        listing.refresh_from_db()
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.REJECTED)
        self.assertEqual(listing.rejection_reason, "Noto'g'ri narx va manzil")

    def test_blocked_user_cannot_login(self):
        """Bloklangan (is_active=False) foydalanuvchi tizimga kira olmasligi."""
        login_url = reverse('auth:login')

        # Dastlab muvaffaqiyatli kiradi
        res = self.client.post(login_url, {
            'email': self.regular_user.email,
            'password': 'StrongPassword123!',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Bloklash
        self.regular_user.is_active = False
        self.regular_user.blocked_reason = "Qoidabuzarlik uchun"
        self.regular_user.blocked_at = timezone.now()
        self.regular_user.save()
        log_admin_action(self.superadmin, "BLOCK_USER", self.regular_user, "Bloklandi")

        # Endi kirish 401 qaytaradi
        res_blocked = self.client.post(login_url, {
            'email': self.regular_user.email,
            'password': 'StrongPassword123!',
        })
        self.assertEqual(res_blocked.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_three_reports_trigger_auto_pending(self):
        """E'longa 3 ta shikoyat tushganda u avtomatik ravishda pending holatiga o'tishi."""
        listing = Listing.objects.create(
            author=self.verified_user,  # Dastlab approved bo'ladi
            title="Zo'r xonadon",
            description="Tavsif",
            city=self.city,
            district=self.district,
            price=1200000,
        )
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.APPROVED)

        # 1-shikoyat
        user1 = User.objects.create_user(email="user1@example.com", password="Pass123!user", first_name="U1")
        Report.objects.create(reporter=user1, reported_listing=listing, reason="Shubhali e'lon")
        listing.refresh_from_db()
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.APPROVED)

        # 2-shikoyat
        user2 = User.objects.create_user(email="user2@example.com", password="Pass123!user", first_name="U2")
        Report.objects.create(reporter=user2, reported_listing=listing, reason="Rasm soxta")
        listing.refresh_from_db()
        self.assertEqual(listing.moderation_status, Listing.ModerationStatus.APPROVED)

        # 3-shikoyat -> Avtomatik PENDING bo'lishi kerak!
        user3 = User.objects.create_user(email="user3@example.com", password="Pass123!user", first_name="U3")
        Report.objects.create(reporter=user3, reported_listing=listing, reason="Firibgarlik gumoni")
        listing.refresh_from_db()
        self.assertEqual(
            listing.moderation_status,
            Listing.ModerationStatus.PENDING,
            "3 ta shikoyatdan keyin e'lon avtomatik PENDING holatiga o'tishi shart!"
        )

    def test_moderator_permissions_restricted(self):
        """Moderator sayt sozlamalari, guruhlar yoki foydalanuvchi qo'shish/o'chirish ruxsatiga ega emasligi."""
        # Moderator e'lonlarni o'zgartirish huquqiga ega
        self.assertTrue(self.moderator.has_perm('listings.change_listing'))
        self.assertTrue(self.moderator.has_perm('reports.change_report'))
        self.assertTrue(self.moderator.has_perm('users.view_user'))

        # Ammo auth.Group, auth.Permission, yoki user qo'shish huquqi YO'Q
        self.assertFalse(self.moderator.has_perm('auth.add_group'))
        self.assertFalse(self.moderator.has_perm('auth.change_group'))
        self.assertFalse(self.moderator.has_perm('auth.delete_group'))
        self.assertFalse(self.moderator.has_perm('users.add_user'))
        self.assertFalse(self.moderator.has_perm('users.delete_user'))

    def test_admin_stats_endpoint(self):
        """GET /api/v1/admin/stats/ endpointi faqat is_staff uchun ishlashi va to'g'ri raqamlar qaytarishi."""
        stats_url = reverse('admin_stats')

        # 1. Anonim foydalanuvchi
        anon_res = self.client.get(stats_url)
        self.assertEqual(anon_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Oddiy foydalanuvchi (is_staff=False)
        self.client.force_authenticate(user=self.regular_user)
        user_res = self.client.get(stats_url)
        self.assertEqual(user_res.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Moderator (is_staff=True)
        self.client.force_authenticate(user=self.moderator)
        mod_res = self.client.get(stats_url)
        self.assertEqual(mod_res.status_code, status.HTTP_200_OK)

        self.assertIn('total_users', mod_res.data)
        self.assertIn('active_listings', mod_res.data)
        self.assertIn('pending_listings', mod_res.data)
        self.assertIn('new_reports', mod_res.data)
        self.assertIn('last_7_days_listings', mod_res.data)
        self.assertIn('last_7_days_users', mod_res.data)
        self.assertIn('listings_by_city', mod_res.data)

