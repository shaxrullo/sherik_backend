from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Moderator guruhi va uning ruxsatlarini avtomatik sozlaydi."

    def handle(self, *args, **options):
        # 1. Moderator guruhini yaratish yoki olish
        moderator_group, created = Group.objects.get_or_create(name='Moderator')
        if created:
            self.stdout.write(self.style.SUCCESS("'Moderator' guruhi yaratildi."))
        else:
            self.stdout.write(self.style.WARNING("'Moderator' guruhi allaqachon mavjud."))

        # 2. Moderator uchun ruxsatlar (faqat e'lonlar, shikoyatlar, foydalanuvchilar va ma'lumotnomalar)
        # Auth Group, Permission, ContentType, Session ruxsatlari BERILMAYDI!
        allowed_permissions = [
            # Listings ilovasi
            ('listings', 'listing', 'view_listing'),
            ('listings', 'listing', 'change_listing'),
            ('listings', 'listing', 'delete_listing'),
            ('listings', 'listingphoto', 'view_listingphoto'),
            ('listings', 'listingphoto', 'change_listingphoto'),
            ('listings', 'listingphoto', 'delete_listingphoto'),

            # Reports ilovasi
            ('reports', 'report', 'view_report'),
            ('reports', 'report', 'change_report'),
            ('reports', 'report', 'delete_report'),

            # Users ilovasi (faqat ko'rish va holatini o'zgartirish)
            ('users', 'user', 'view_user'),
            ('users', 'user', 'change_user'),
            ('users', 'lifestylepreference', 'view_lifestylepreference'),
            ('users', 'adminactionlog', 'view_adminactionlog'),
            ('users', 'city', 'view_city'),
            ('users', 'district', 'view_district'),

            # Favorites ilovasi (ko'rish)
            ('favorites', 'favorite', 'view_favorite'),
        ]

        permissions_to_assign = []
        for app_label, model, codename in allowed_permissions:
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                perm = Permission.objects.get(content_type=ct, codename=codename)
                permissions_to_assign.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stdout.write(self.style.ERROR(f"Ruxsat topilmadi: {app_label}.{codename}"))

        # Guruhga biriktirish
        moderator_group.permissions.set(permissions_to_assign)
        self.stdout.write(self.style.SUCCESS(
            f"'Moderator' guruhiga jami {len(permissions_to_assign)} ta ruxsat muvaffaqiyatli biriktirildi."
        ))

