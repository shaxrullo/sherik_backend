from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, LifestylePreference, City, District, AdminActionLog
from .services import log_admin_action


class LifestylePreferenceInline(admin.StackedInline):
    model = LifestylePreference
    can_delete = False
    verbose_name = "Turmush tarzi afzalliklari"
    verbose_name_plural = "Turmush tarzi afzalliklari"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    search_fields = ['name', 'slug']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'is_active']
    search_fields = ['name', 'city__name']
    list_filter = ['city', 'is_active']
    list_select_related = ['city']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display = [
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'role',
        'city',
        'is_verified',
        'is_active',
        'is_staff',
        'date_joined',
    ]
    list_filter = [
        'is_active',
        'is_verified',
        'role',
        'gender',
        'city',
        'is_staff',
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number', 'telegram_username']
    list_select_related = ['city', 'district']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Shaxsiy ma\'lumotlar', {
            'fields': (
                'first_name',
                'last_name',
                'phone_number',
                'is_phone_verified',
                'gender',
                'city',
                'district',
                'birth_year',
                'role',
                'telegram_username',
                'avatar',
                'bio',
            )
        }),
        ('Ishonch va moderatsiya', {
            'fields': (
                'is_verified',
                'is_active',
                'blocked_reason',
                'blocked_at',
            )
        }),
        ('Ruxsatlar', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Muhim sanalar', {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
    )
    readonly_fields = ('date_joined', 'updated_at', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    inlines = [LifestylePreferenceInline]
    actions = ['make_verified', 'block_users', 'unblock_users']

    @admin.action(description="Tanlanganlarni ishonchli (verified) deb belgilash")
    def make_verified(self, request, queryset):
        count = queryset.update(is_verified=True)
        for user in queryset:
            log_admin_action(request, "VERIFY_USER", user, "Foydalanuvchi tasdiqlangan deb belgilandi")
        self.message_user(request, f"{count} ta foydalanuvchi tasdiqlangan (verified) deb belgilandi.")

    @admin.action(description="Tanlangan foydalanuvchilarni bloklash")
    def block_users(self, request, queryset):
        # Superadmin o'zini bloklab qo'ymasligi uchun
        non_superusers = queryset.exclude(is_superuser=True)
        count = non_superusers.update(
            is_active=False,
            blocked_reason="Admin/Moderator tomonidan bloklandi",
            blocked_at=timezone.now(),
        )
        for user in non_superusers:
            log_admin_action(request, "BLOCK_USER", user, "Foydalanuvchi tizimdan bloklandi")
        self.message_user(request, f"{count} ta foydalanuvchi bloklandi.")

    @admin.action(description="Tanlanganlarni blokdan chiqarish")
    def unblock_users(self, request, queryset):
        count = queryset.update(
            is_active=True,
            blocked_reason="",
            blocked_at=None,
        )
        for user in queryset:
            log_admin_action(request, "UNBLOCK_USER", user, "Foydalanuvchi blokdan chiqarildi")
        self.message_user(request, f"{count} ta foydalanuvchi blokdan chiqarildi.")


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'target_model', 'target_id', 'target_repr', 'ip_address']
    list_filter = ['action', 'target_model', 'created_at']
    search_fields = ['user__email', 'target_repr', 'details', 'ip_address']
    list_select_related = ['user']
    readonly_fields = [
        'created_at',
        'user',
        'action',
        'target_model',
        'target_id',
        'target_repr',
        'details',
        'ip_address',
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
