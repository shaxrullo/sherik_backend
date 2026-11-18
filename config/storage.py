import mimetypes
import os
import uuid
import requests
from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    """Supabase Storage REST API orqali media fayllarni doimiy saqlash."""

    def __init__(self, url=None, key=None, bucket=None):
        self.base_url = (url or settings.SUPABASE_URL).rstrip('/')
        self.api_key = (key or settings.SUPABASE_KEY).strip()
        self.bucket = (bucket or getattr(settings, 'SUPABASE_BUCKET', 'media')).strip()

    def _headers(self, content_type=None):
        headers = {
            'apikey': self.api_key,
        }
        # Legacy JWT service_role kaliti (eyJ...) uchun Authorization: Bearer kerak;
        # Yangi sb_secret_... kalitlari ham apikey orqali ishlaydi
        if not self.api_key.startswith('sb_secret_'):
            headers['Authorization'] = f'Bearer {self.api_key}'
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def _normalize_name(self, name):
        return name.replace('\\', '/').lstrip('/')

    def get_available_name(self, name, max_length=None):
        name = self._normalize_name(name)
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        suffix = uuid.uuid4().hex[:8]
        unique_name = f"{file_root}_{suffix}{file_ext}"
        full_name = f"{dir_name}/{unique_name}" if dir_name else unique_name

        if max_length and len(full_name) > max_length:
            extra_len = len(dir_name) + (1 if dir_name else 0) + len(file_ext) + len(suffix) + 1
            allowed_root = max(1, max_length - extra_len)
            unique_name = f"{file_root[:allowed_root]}_{suffix}{file_ext}"
            full_name = f"{dir_name}/{unique_name}" if dir_name else unique_name

        return full_name

    def _save(self, name, content):
        clean_name = self._normalize_name(name)
        content_type = getattr(content, 'content_type', None)
        if not content_type:
            content_type, _ = mimetypes.guess_type(clean_name)
        content_type = content_type or 'application/octet-stream'

        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()

        upload_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{clean_name}"
        headers = self._headers(content_type=content_type)
        headers['x-upsert'] = 'true'

        response = requests.post(upload_url, headers=headers, data=data, timeout=30)
        if response.status_code not in (200, 201):
            raise IOError(
                f"Supabase Storage yuklashda xatolik ({response.status_code}): {response.text}"
            )
        return clean_name

    def delete(self, name):
        if not name:
            return
        clean_name = self._normalize_name(name)
        delete_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{clean_name}"
        try:
            requests.delete(delete_url, headers=self._headers(), timeout=15)
        except requests.RequestException:
            pass

    def exists(self, name):
        # get_available_name har doim unikal nom yaratadi
        return False

    def url(self, name):
        clean_name = self._normalize_name(name)
        return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{clean_name}"
