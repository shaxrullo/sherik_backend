# Sherik Topish — Backend API

O'zbekistonda birga yashash uchun sherik (roommate) va ijaraga turar-joy topish platformasining backend tizimi (REST API).

## 🛠 Texnologiyalar steki

* **Backend Framework:** Django 5.1, Django REST Framework (DRF)
* **Autentifikatsiya:** JWT (djangorestframework-simplejwt) & Google OAuth 2.0
* **Ma'lumotlar bazasi:** PostgreSQL 16 (Docker Compose)
* **API Hujjatlari:** drf-spectacular (Swagger UI / Redoc)
* **Konteynerizatsiya:** Docker & Docker Compose

---

## 🚀 Loyihani ishga tushirish

### 1. Repozitoriyani klonlash
```bash
git clone https://github.com/shaxrullo/sherik_backend.git
cd sherik_backend
```

### 2. Virtual muhitni faollashtirish va bog'liqliklarni o'rnatish
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Muhit o'zgaruvchilarini sozlash (.env)
`.env.example` faylidan nusxa olib `.env` faylini yarating va kerakli ma'lumotlarni kiriting:
```bash
cp .env.example .env
```

### 4. PostgreSQL bazasini ishga tushirish (Docker)
```bash
docker compose up -d
```

### 5. Migratsiyalarni qo'llash va rollarni yaratish
```bash
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
```

### 6. Serverni ishga tushirish
```bash
python manage.py runserver
```

---

## 📖 API Hujjatlari

Server ishga tushirilgach, quyidagi havolalar orqali API spetsifikatsiyasi bilan tanishishingiz mumkin:
* **Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
* **Redoc:** [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
* **OpenAPI Schema (JSON):** [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

## 🧪 Testlarni ishga tushirish

Barcha modullar (Users, Listings, Favorites, Reports, Matching) bo'yicha birlik testlarni ishga tushirish:
```bash
python manage.py test
```

---

## 🌐 Render.com'ga deploy qilish (Production)

Render.com da Web Service yaratishda quyidagi sozlamalardan foydalaning:
* **Environment:** Python 3
* **Build Command:**
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
  ```
* **Start Command:**
  ```bash
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ```
* **Environment Variables:**
  * `DEBUG`: `False`
  * `SECRET_KEY`: `maxfiy-kalit`
  * `DATABASE_URL`: `Render PostgreSQL Internal Connection String`
  * `ALLOWED_HOSTS`: `.onrender.com,localhost,127.0.0.1`
  * `ADMIN_URL`: `secret-admin/` (yoki o'zingiz istagan maxfiy yo'l)


