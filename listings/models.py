from django.db import models
from django.utils import timezone
from django.conf import settings


class Listing(models.Model):
    """Uy-joy va sheriklik e'loni modeli."""

    class ListingType(models.TextChoices):
        HAVE_ROOM = 'have_room', "Joy bor (Sherik kerak)"
        NEED_ROOM = 'need_room', "Joy kerak (Ijara qidiryapti)"

    class GenderPreference(models.TextChoices):
        MALE = 'male', "Faqat erkaklar / yigitlar"
        FEMALE = 'female', "Faqat ayollar / qizlar"
        ANY = 'any', "Farqi yo'q"

    class Status(models.TextChoices):
        ACTIVE = 'active', "Faol"
        CLOSED = 'closed', "Yopilgan"

    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', "Kutilmoqda"
        APPROVED = 'approved', "Tasdiqlangan"
        REJECTED = 'rejected', "Rad etilgan"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name="Muallif",
    )
    listing_type = models.CharField(
        max_length=20,
        choices=ListingType.choices,
        default=ListingType.HAVE_ROOM,
        verbose_name="E'lon turi",
    )
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Tavsif")
    city = models.ForeignKey(
        'users.City',
        on_delete=models.PROTECT,
        related_name='listings',
        verbose_name="Shahar",
    )
    district = models.ForeignKey(
        'users.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
        verbose_name="Tuman",
    )
    address_line = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Aniq manzil yoki mo'ljal",
    )
    class Currency(models.TextChoices):
        USD = 'USD', "USD ($)"
        UZS = 'UZS', "UZS (so'm)"

    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Oylik narx",
        help_text="Masalan 100 yoki 1500000",
    )
    currency = models.CharField(
        max_length=5,
        choices=Currency.choices,
        default=Currency.USD,
        verbose_name="Valyuta",
    )
    capacity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Nechta kishiga mo'ljallangan / kerak",
    )
    total_residents = models.PositiveSmallIntegerField(
        default=1,
        null=True,
        blank=True,
        verbose_name="Umumiy yashovchilar soni (jami)",
        help_text="Kvartirada jami yashovchilar soni",
    )
    gender_preference = models.CharField(
        max_length=10,
        choices=GenderPreference.choices,
        default=GenderPreference.ANY,
        verbose_name="Jinsi bo'yicha talab",
    )
    amenities = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Qulayliklar va jihozlar",
        help_text="Masalan: ['Wi-Fi', 'Konditsioner', 'Kir yuvish mashinasi']",
    )
    near_subway = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Yaqin metro bekati",
        help_text="Masalan: Chilonzor, Novza yoki bo'sh",
    )
    nearby_universities = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Yaqin o'qish joylari (OTM)",
        help_text="Masalan: ['TATU', 'O'zMU', 'TDTU']",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="E'lon holati",
    )

    # Moderatsiya qismi (Default: Darhol tasdiqlanadi - Approved)
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.APPROVED,
        verbose_name="Moderatsiya holati",
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Rad etish sababi",
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_listings',
        verbose_name="Moderator",
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Moderatsiya qilingan sana",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan sana")

    class Meta:
        verbose_name = "E'lon"
        verbose_name_plural = "E'lonlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='listings_created_idx'),
            models.Index(fields=['status'], name='listings_status_idx'),
            models.Index(fields=['moderation_status'], name='listings_mod_status_idx'),
            models.Index(fields=['author_id'], name='listings_author_idx'),
            models.Index(fields=['city_id'], name='listings_city_idx'),
            models.Index(fields=['district_id'], name='listings_district_idx'),
            models.Index(fields=['listing_type'], name='listings_type_idx'),
            models.Index(fields=['status', 'moderation_status'], name='listings_status_mod_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_listing_type_display()}) - {self.city.name}"

    def save(self, *args, **kwargs):
        # Barcha yangi e'lonlar avtomatik ravishda tasdiqlangan (APPROVED) holatda chiqadi
        if not self.pk:
            self.moderation_status = self.ModerationStatus.APPROVED
            if not self.moderated_at:
                self.moderated_at = timezone.now()
        super().save(*args, **kwargs)


class ListingPhoto(models.Model):
    """E'lon rasmi modeli."""

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="E'lon",
    )
    image = models.ImageField(
        upload_to='listings/%Y/%m/',
        verbose_name="Rasm",
    )
    is_main = models.BooleanField(
        default=False,
        verbose_name="Asosiy rasm",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan sana")

    class Meta:
        verbose_name = "E'lon rasmi"
        verbose_name_plural = "E'lon rasmlari"
        ordering = ['-is_main', 'id']
        indexes = [
            models.Index(fields=['listing_id'], name='photo_listing_idx'),
            models.Index(fields=['is_main'], name='photo_main_idx'),
        ]

    def __str__(self):
        return f"{self.listing.title} rasmi"
