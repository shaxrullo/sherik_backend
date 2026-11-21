"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
import logging

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Render Free Plan va har qanday serverda avtomatik migratsiya va admin yaratish
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)

    from users.models import User
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@sherik.uz')
    admin_pass = os.environ.get('ADMIN_PASSWORD')

    user, created = User.objects.get_or_create(email=admin_email, defaults={'first_name': 'Admin'})
    user.is_staff = True
    user.is_superuser = True
    if admin_pass:
        user.set_password(admin_pass)
        user.save()
        print(f'>>> Auto-migration: Admin paroli ADMIN_PASSWORD orqali yangilandi: {admin_email} <<<', file=sys.stdout)
    elif created:
        user.set_password('SherikAdmin2026!Secure')
        user.save()
        print(f'>>> Auto-migration: Yangi admin yaratildi: {admin_email} <<<', file=sys.stdout)
    else:
        print('>>> Auto-migration muvaffaqiyatli bajarildi! <<<', file=sys.stdout)
except Exception as e:
    logging.exception('WSGI auto-migration error: %s', e)
