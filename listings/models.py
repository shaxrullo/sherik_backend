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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="E'lon holati",
    )

    # Moderatsiya qismi
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
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

    def __str__(self):
        return f"{self.title} ({self.get_listing_type_display()}) - {self.city.name}"

    def save(self, *args, **kwargs):
        # Allaqachon tasdiqlangan ishonchli foydalanuvchilar (is_verified=True) yoki admin/moderatorlar e'loni avtomatik approved bo'ladi
        if not self.pk:
            author = getattr(self, 'author', None)
            if not author and self.author_id:
                from django.contrib.auth import get_user_model
                author = get_user_model().objects.filter(pk=self.author_id).first()
            if author and (getattr(author, 'is_verified', False) or getattr(author, 'is_staff', False)):
                self.moderation_status = self.ModerationStatus.APPROVED
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

    def __str__(self):
        return f"{self.listing.title} rasmi"
