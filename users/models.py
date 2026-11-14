from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.text import slugify


class City(models.Model):
    """Shahar ma'lumotnomasi."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Shahar nomi")
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name="Slug")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Shahar"
        verbose_name_plural = "Shaharlar"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class District(models.Model):
    """Tuman ma'lumotnomasi."""
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='districts',
        verbose_name="Shahar",
    )
    name = models.CharField(max_length=100, verbose_name="Tuman nomi")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Tuman"
        verbose_name_plural = "Tumanlar"
        unique_together = ('city', 'name')
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class UserManager(BaseUserManager):
    """Maxsus foydalanuvchi menejeri: email asosiy login hisoblanadi."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email kiritilishi shart.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Foydalanuvchi modeli."""

    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    class Role(models.TextChoices):
        SEEKER = 'seeker', "Sherik/Joy qidiruvchi (talaba/ishlovchi)"
        HOST = 'host', "Joy egasi / Asosiy ijarachi"

    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name="Email manzili",
        help_text="Tizimga kirish uchun asosiy identifikator",
    )
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Familiya")
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefon raqami",
        help_text="Masalan: +998901234567",
    )
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name="Telefon tasdiqlangan",
        help_text="Keyinchalik SMS/Telegram orqali tasdiqlash uchun belgi",
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        verbose_name="Jinsi",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Shahar",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Tuman",
    )
    birth_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tug'ilgan yili",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.SEEKER,
        verbose_name="Foydalanuvchi roli",
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram foydalanuvchi nomi",
        help_text="Masalan: @foydalanuvchi",
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Profil rasmi",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="O'zi haqida qisqacha ma'lumot",
    )

    # Moderatsiya va ishonch belgilari
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Tasdiqlangan foydalanuvchi (ishonch belgisi)",
        help_text="Tasdiqlangan foydalanuvchilarning e'lonlari avtomatik approved bo'ladi",
    )
    blocked_reason = models.TextField(
        blank=True,
        verbose_name="Bloklash sababi",
    )
    blocked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloklangan sana",
    )

    # Standart tizim maydonlari
    is_active = models.BooleanField(default=True, verbose_name="Faol (bloklanmagan)")
    is_staff = models.BooleanField(default=False, verbose_name="Xodim maqomi (Admin/Moderator)")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tahrirlangan sana")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ['-date_joined']

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email


class LifestylePreference(models.Model):
    """
    Turmush tarzi afzalliklari (chekish, tozalik, uyga kelish vaqti, hayvonlar, mehmonlar).
    Moslik (matching) algoritmi uchun foydalaniladi.
    """

    class Smoking(models.TextChoices):
        NO = 'no', "Chekmayman / Chekilmasin"
        YES = 'yes', "Chekaman / Ruxsat"
        OUTSIDE = 'outside', "Faqat tashqarida/balkonda"

    class Cleanliness(models.TextChoices):
        VERY_CLEAN = 'very_clean', "Juda tartibli va toza"
        MODERATE = 'moderate', "O'rtacha tozalik"
        RELAXED = 'relaxed', "Erkin / Qat'iy emas"

    class Pets(models.TextChoices):
        NO = 'no', "Hayvonlarga qarshiman"
        YES = 'yes', "Uy hayvoni bor / Yoqtiraman"
        INDIFFERENT = 'indifferent', "Farqi yo'q"

    class Guests(models.TextChoices):
        NO = 'no', "Mehmon kutish mumkin emas"
        RARELY = 'rarely', "Faqat ogohlantirish bilan / Kamdan-kam"
        WELCOME = 'welcome', "Erkin / Ruxsat"

    class SleepSchedule(models.TextChoices):
        EARLY_BIRD = 'early_bird', "Erta yotib, erta turuvchi (tonggi)"
        NIGHT_OWL = 'night_owl', "Kech yotuvchi (tungi)"
        FLEXIBLE = 'flexible', "Moslashuvchan"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='lifestyle',
        verbose_name="Foydalanuvchi",
    )
    smoking = models.CharField(
        max_length=20,
        choices=Smoking.choices,
        default=Smoking.NO,
        verbose_name="Chekishga munosabat",
    )
    cleanliness = models.CharField(
        max_length=20,
        choices=Cleanliness.choices,
        default=Cleanliness.MODERATE,
        verbose_name="Tozalik va tartib",
    )
    curfew = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Uyga kelish vaqti",
        help_text="Masalan: Soat 22:00 gacha, yoki Cheklov yo'q",
    )
    pets = models.CharField(
        max_length=20,
        choices=Pets.choices,
        default=Pets.INDIFFERENT,
        verbose_name="Uy hayvonlariga munosabat",
    )
    guests = models.CharField(
        max_length=20,
        choices=Guests.choices,
        default=Guests.RARELY,
        verbose_name="Mehmon olib kelish",
    )
    sleep_schedule = models.CharField(
        max_length=20,
        choices=SleepSchedule.choices,
        default=SleepSchedule.FLEXIBLE,
        verbose_name="Uyqu rejimi",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Qo'shimcha odatlar yoki talablar",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        verbose_name = "Turmush tarzi afzalligi"
        verbose_name_plural = "Turmush tarzi afzalliklari"

    def __str__(self):
        return f"{self.user.email} turmush tarzi"


class AdminActionLog(models.Model):
    """Moderator va Adminlarning harakatlari jurnali (Audit)."""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='action_logs',
        verbose_name="Moderator / Admin",
    )
    action = models.CharField(max_length=100, verbose_name="Harakat turi")
    target_model = models.CharField(max_length=50, verbose_name="Obyekt modeli")
    target_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Obyekt ID")
    target_repr = models.CharField(max_length=255, verbose_name="Obyekt tavsifi")
    details = models.TextField(blank=True, verbose_name="Tafsilotlar / Sabab")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP manzil")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Bajarilgan sana va vaqt")

    class Meta:
        verbose_name = "Admin harakatlar jurnali"
        verbose_name_plural = "Admin harakatlar jurnallari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
