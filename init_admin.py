import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

email = os.environ.get('ADMIN_EMAIL', 'admin@sherik.uz')
password = os.environ.get('ADMIN_PASSWORD', 'admin12345')

user, created = User.objects.get_or_create(email=email, defaults={'first_name': 'Admin'})
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

if created:
    print(f'>>> Superuser {email} muvaffaqiyatli yaratildi!')
else:
    print(f'>>> Superuser {email} paroli muvaffaqiyatli yangilandi!')

