# Sherik Topish — Backend API

O'zbekistonda birga yashash uchun sherik (roommate) va ijaraga turar-joy topish platformasining backend tizimi (REST API).

## ✨ Production-Ready Backend (Updated Nov 22, 2026)

**Status**: MVP → Production-Ready Upgrade ✅

Tezda 10 ta muhim uzatishni bajarish:
- ✅ Database performance indexes
- ✅ Health check endpoints  
- ✅ Standardized error handling
- ✅ GitHub Actions CI/CD
- ✅ 70%+ test coverage
- ✅ Redis caching for matching
- ✅ Sentry error monitoring
- ✅ Complete API documentation
- ✅ Linting & code quality tools
- ✅ Deployment checklist

**Complete Details**: [`URGENT_TASKS_SUMMARY.md`](./URGENT_TASKS_SUMMARY.md)

---

## 🛠 Texnologiyalar steki

* **Backend Framework:** Django 5.1, Django REST Framework (DRF)
* **Autentifikatsiya:** JWT (djangorestframework-simplejwt) & Google OAuth 2.0
* **Ma'lumotlar bazasi:** PostgreSQL 16
* **Cache:** Redis (production), Local Memory (development)
* **Monitoring:** Sentry (error tracking)
* **API Hujjatlari:** drf-spectacular (Swagger UI / Redoc)
* **Code Quality:** Black, isort, flake8, bandit
* **Testing:** pytest, pytest-cov
* **CI/CD:** GitHub Actions
* **Containerization:** Docker & Docker Compose

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
`.env.example` faylidan nusxa olib `.env` faylini yarating:
```bash
cp .env.example .env
# Kerakli ma'lumotlarni kiriting
```

### 4. Redis'ni o'rnatish (optional, production uchun tavsiya)
```bash
# Docker bilan
docker run -d -p 6379:6379 redis:latest

# Yoki OS'ga o'rnatish
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
# Windows: WSL orqali yoki Redis for Windows
```

### 5. PostgreSQL bazasini ishga tushirish (Docker)
```bash
docker compose up -d
```

### 6. Migratsiyalarni qo'llash
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Pre-commit hooks o'rnatish (tavsiya)
```bash
pip install pre-commit
pre-commit install
```

### 8. Serverni ishga tushirish
```bash
python manage.py runserver
```

---

## 📖 API Hujjatlari

Server ishga tushirilgach:
* **Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
* **Redoc:** [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
* **API Dokumentatsiya:** [`docs/API_DOCUMENTATION.md`](./docs/API_DOCUMENTATION.md)
* **Health Checks:**
  - `GET /health/` - Basic health
  - `GET /ready/` - Readiness probe
  - `GET /alive/` - Liveness probe

---

## 🧪 Testlarni ishga tushirish

```bash
# Barcha testlarni ishga tushirish
pytest

# Coverage bilan
pytest --cov=. --cov-report=html

# Faqat bitta modul
pytest listings/tests.py

# Verbose rejimda
pytest -v
```

---

## 🔍 Code Quality

### Linting va Formatting

```bash
# Barcha quality checklarni ishga tushirish
./scripts/lint.sh

# Kodni avtomatik formatlash
./scripts/format.sh

# Manual checks
black .           # Format kodi
isort .           # Import tartibi
flake8 .          # Linting
bandit -r .       # Security check
```

### Pre-commit Hooks

```bash
# O'rnatish
pre-commit install

# Barcha fayllarni tekshirish
pre-commit run --all-files
```

---

## 🔐 Monitoring va Xatolar

### Sentry Integration

Sentry'ni setup qilish uchun [`docs/SENTRY_SETUP.md`](./docs/SENTRY_SETUP.md) ni o'qing.

Environment variable'larni sozlash:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
```

Monitoring endpoints:
- `GET /monitoring/status/` - Monitoring holati
- `POST /monitoring/sentry-test/` - Test Sentry

---

## 🌐 Render.com'ga Deploy qilish

### Environment Variables

```bash
DEBUG=False
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production
ALLOWED_HOSTS=yourdomain.com
SECURE_SSL_REDIRECT=True
```

### Build & Start Commands

**Build:**
```bash
pip install -r requirements.txt && \
python manage.py collectstatic --no-input && \
python manage.py migrate --noinput
```

**Start:**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Deployment Checklist

Deployment uchun [`docs/DEPLOYMENT_CHECKLIST.md`](./docs/DEPLOYMENT_CHECKLIST.md) ni o'qing.

---

## 📁 Proyekt Struktura

```
sherik_backend/
├── config/              # Django sozlamalari
│   ├── settings.py      # Asosiy sozlamalar
│   ├── urls.py          # URL yo'llanishi
│   ├── wsgi.py          # WSGI applikatsiyasi
│   ├── health.py        # Health check endpoints
│   ├── exceptions.py     # Custom exception handlers
│   ├── monitoring.py    # Sentry va monitoring
│   └── cache_utils.py   # Cache utilities
│
├── listings/            # E'lon ilovasi
│   ├── models.py        # Listing, ListingPhoto
│   ├── views.py         # Listing API views
│   ├── serializers.py   # Listing serializers
│   ├── tests.py         # Listing testlari
│   └── migrations/      # Database migrations
│
├── users/               # Foydalanuvchi ilovasi
│   ├── models.py        # User, City, District
│   ├── views.py         # Auth endpoints
│   └── migrations/
│
├── favorites/           # Sevimlilar ilovasi
│   ├── models.py        # Favorite model
│   ├── views.py         # Favorite endpoints
│   └── migrations/
│
├── reports/             # Shikoyatlar ilovasi
│   ├── models.py        # Report model
│   ├── views.py         # Report endpoints
│   └── migrations/
│
├── matching/            # Moslik tavsiyalari
│   ├── models.py        # (empty - bu yerda logic yo'q)
│   ├── services.py      # Matching algoritm
│   ├── services_cached.py # Cached matching
│   ├── views.py         # Recommendation endpoints
│   └── serializers.py
│
├── docs/                # Dokumentatsiya
│   ├── API_DOCUMENTATION.md
│   ├── SENTRY_SETUP.md
│   ├── CODE_QUALITY.md
│   └── DEPLOYMENT_CHECKLIST.md
│
├── scripts/             # Utility scriptlari
│   ├── lint.sh          # Code quality checks
│   └── format.sh        # Auto-format code
│
├── .github/
│   └── workflows/       # GitHub Actions
│       ├── tests.yml    # Test va linting CI
│       └── deploy.yml   # Deployment automation
│
├── requirements.txt     # Python dependencies
├── manage.py            # Django CLI
├─��� pytest.ini           # Pytest config
├── .flake8              # Flake8 config
├── .pre-commit-config.yaml
├── pyproject.toml       # Black/isort config
├── URGENT_TASKS_SUMMARY.md  # Completion summary
└── README.md            # This file
```

---

## 🔗 Muhim Havolalar

- **GitHub**: [sherik_backend](https://github.com/shaxrullo/sherik_backend)
- **Render**: [https://sherik-backend.onrender.com](https://sherik-backend.onrender.com)
- **Admin Panel**: [https://sherik-backend.onrender.com/secret-admin/](https://sherik-backend.onrender.com/secret-admin/)

---

## 📚 Dokumentatsiya

- [`URGENT_TASKS_SUMMARY.md`](./URGENT_TASKS_SUMMARY.md) - Completion details
- [`docs/API_DOCUMENTATION.md`](./docs/API_DOCUMENTATION.md) - Complete API reference
- [`docs/SENTRY_SETUP.md`](./docs/SENTRY_SETUP.md) - Error monitoring setup
- [`docs/CODE_QUALITY.md`](./docs/CODE_QUALITY.md) - Code standards
- [`docs/DEPLOYMENT_CHECKLIST.md`](./docs/DEPLOYMENT_CHECKLIST.md) - Safe deployment

---

## 🤝 Jamoaga Qo'shilish

1. Forkini yarating
2. Feature branch yarating (`git checkout -b feature/amazing-feature`)
3. Commitlarini qo'ying (`git commit -m 'Add amazing feature'`)
4. Branchga push qo'ying (`git push origin feature/amazing-feature`)
5. Pull Request ochib qo'ying

**Code Quality Standards**:
- ✅ 70%+ test coverage
- ✅ All linting checks passing
- ✅ Black formatted code
- ✅ Bandit security scan passed
- ✅ Documentation updated

---

## 📞 Bog'lanish

- **GitHub Issues**: [Issues](https://github.com/shaxrullo/sherik_backend/issues)
- **Email**: [your-email@example.com]

---

## 📄 Litsenziya

Ushbu proyekt [MIT License](LICENSE) ostida litsenziyalangan.

---

**Oxirgi yangilash**: November 22, 2026 ✅  
**Status**: Production-Ready 🚀  
**Version**: 1.0.0


