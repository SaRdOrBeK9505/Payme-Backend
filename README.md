# Payme Backend - Django + DRF + Firebase

Telegram Mini App uchun Payme to'lov tizimi integratsiyasi.

## 🚀 Tezkor Boshlash

### 1. Dependencies O'rnatish

```bash
pip install -r requirements.txt
```

### 2. Environment Variables Sozlash

`.env` faylini tahrirlang:

```env
PAYME_MERCHANT_ID=your_merchant_id
PAYME_KEY=your_payme_key
```

### 3. Firebase Service Account

`secrets/firebase-service-account.json` faylini Firebase Console'dan yuklab oling va joylashtiring.

### 4. Django Migratsiyalari

```bash
python manage.py migrate
```

### 5. Serverni Ishga Tushirish

```bash
python manage.py runserver
```

## 📚 API Dokumentatsiya (Swagger)

Server ishga tushganidan keyin:

- **Swagger UI (Interactive):** http://localhost:8000/api/docs/
- **ReDoc (Alternative):** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

Swagger UI'da barcha endpoint'larni ko'rish va "Try it out" funksiyasi bilan to'g'ridan-to'g'ri test qilish mumkin!

## 🔗 API Endpoints

- `POST /api/payments/create-link/` - To'lov havolasini yaratish
- `POST /api/payments/webhook/` - Payme webhook (Merchant API)

## 📖 Hujjatlar

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Batafsil o'rnatish qo'llanmasi
- [PAYME_INTEGRATION_GUIDE.md](PAYME_INTEGRATION_GUIDE.md) - To'liq integratsiya
- [TESTING_EXAMPLES.md](TESTING_EXAMPLES.md) - Test misollar
- [SWAGGER_GUIDE.md](SWAGGER_GUIDE.md) - Swagger/OpenAPI qo'llanmasi
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arxitektura hujjatlari
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Loyiha xulosasi

## 📦 Texnologiyalar

- **Backend:** Django 4.2, Django REST Framework
- **Database:** Firebase Firestore
- **To'lov:** Payme Merchant API (JSON-RPC 2.0)
- **API Docs:** drf-spectacular (Swagger/OpenAPI 3.0)
- **Python:** 3.9+

## 🔒 Xavfsizlik

- ✅ Basic Authentication (Paycom:KEY)
- ✅ IP Whitelist
- ✅ Firebase Admin SDK
- ✅ Environment variables (.env)

## 🧪 Test Qilish

```bash
# Quick start test
python quick_start.py

# Unit tests
python manage.py test payments

# Swagger UI'da test qilish
# http://localhost:8000/api/docs/ → "Try it out"
```

## 📄 Litsenziya

MIT License
