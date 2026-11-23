import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

count_blocked = 0
count_kept = 0

for user in User.objects.all():
    username = (getattr(user, 'telegram_username', '') or '').strip().lstrip('@').lower()
    if username == 'id_441':
        user.is_active = True
        user.save(update_fields=['is_active'])
        count_kept += 1
        print(f"✅ Ruxsat berildi: ID {user.id} - @{username}")
    else:
        user.is_active = False
        user.save(update_fields=['is_active'])
        count_blocked += 1
        print(f"⛔ Bloklandi: ID {user.id} - {user.email} (tg: {user.telegram_username})")

print(f"Yakunlandi: {count_kept} ta faol (@id_441), {count_blocked} ta foydalanuvchi bloklandi.")
