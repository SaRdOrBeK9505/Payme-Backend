# Payme Backend - O'rnatish Qo'llanmasi

Django + DRF + Firebase + Payme integratsiyasini to'liq ishga tushirish bo'yicha bosqichma-bosqich qo'llanma.

## 📦 1. Python va Virtual Environment

### Python versiyasini tekshirish
```bash
python --version
# Minimal: Python 3.9+
```

### Virtual environment yaratish
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

## 📚 2. Dependencies O'rnatish

```bash
pip install -r requirements.txt
```

Agar xato yuzaga kelsa, package'larni alohida o'rnating:

```bash
pip install Django==4.2.0
pip install djangorestframework
pip install firebase-admin
pip install python-decouple
pip install google-cloud-firestore
pip install pytz
```

## 🔥 3. Firebase Setup

### 3.1. Firebase Loyihasi Yaratish

1. [Firebase Console](https://console.firebase.google.com/)ga kiring
2. "Add project" tugmasini bosing
3. Loyiha nomini kiriting (masalan: `payme-backend`)
4. Google Analytics'ni o'chirib qo'yishingiz mumkin (ixtiyoriy)
5. "Create project" bosing

### 3.2. Firestore Database Yaratish

1. Firebase Console → Build → Firestore Database
2. "Create database" bosing
3. Location: `europe-west3` (yoki sizga eng yaqin region)
4. Start in **production mode** (security rules'ni keyinroq sozlaymiz)

### 3.3. Service Account Key Olish

1. Firebase Console → Project Settings (⚙️ icon)
2. Service Accounts tab
3. "Generate new private key" tugmasini bosing
4. JSON fayl yuklab olinadi
5. Bu faylni loyihangizda `secrets/firebase-service-account.json` ga nusxalang

**Muhim:** `secrets/` papkani yarating va JSON faylni u yerga joylashtiring:

```bash
# Windows
mkdir secrets
copy C:\Downloads\your-project-firebase-adminsdk.json secrets\firebase-service-account.json

# Linux/Mac
mkdir secrets
cp ~/Downloads/your-project-firebase-adminsdk.json secrets/firebase-service-account.json
```

### 3.4. Firestore Security Rules

Firebase Console → Firestore Database → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Orders - authenticated users
    match /orders/{orderId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    
    // Transactions - server only (via Admin SDK)
    match /transactions/{transactionId} {
      allow read: if request.auth != null;
      allow write: if false; // Only server can write
    }
  }
}
```

"Publish" tugmasini bosing.

### 3.5. Test Order Yaratish

Firestore Console → Data → Start collection:

**Collection ID:** `orders`

**Document ID:** `ORD-TEST-001`

**Fields:**
```
orderId: "ORD-TEST-001" (string)
status: "pending" (string)
total: 50000 (number)
totalItems: 1 (number)
address: "Test address" (string)
phone: "+998901234567" (string)
region: "Toshkent" (string)
payment: "Payme" (string)
delivery: "Kuryer" (string)
createdAt: 1700000000000 (number)
items: [] (array)
```

## 💳 4. Payme Setup

### 4.1. Payme Akkaunt Yaratish

1. [Payme Merchant](https://merchant.payme.uz/)ga ro'yxatdan o'ting
2. Kompaniya ma'lumotlarini to'ldiring
3. Hujjatlarni yuklang va tasdiqlanishini kuting

### 4.2. Merchant ID va Key Olish

1. Payme Merchant Cabinet → Settings
2. **Merchant ID**ni nusxalang
3. Settings → API → **Secret Key**ni generate qiling va nusxalang

### 4.3. Webhook URL Sozlash

1. Payme Merchant Cabinet → Settings → Endpoints
2. **Endpoint URL:** `https://your-domain.com/api/payments/webhook/`
   - Local test uchun: ngrok yoki localtunnel ishlatishingiz kerak
3. **Method:** POST
4. Save va Test qiling

### 4.4. Test Muhit

Payme test muhiti uchun:
- **Test Checkout URL:** `https://checkout.test.paycom.uz/`
- **Test Karta:** `8600 0000 0000 0000`
- **Muddati:** `03/99`
- **SMS Kod:** `666666`

## ⚙️ 5. Environment Variables (.env)

`.env` faylini loyiha root'ida yarating va to'ldiring:

```env
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Payme Configuration
PAYME_MERCHANT_ID=your_merchant_id_from_payme_cabinet
PAYME_KEY=your_secret_key_from_payme_cabinet
PAYME_ACCOUNT_FIELD=order_id

# Payme IP Whitelist (Production uchun)
# Test muhitda bo'sh qoldiring
PAYME_ALLOWED_IPS=

# Production uchun:
# PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

**Django SECRET_KEY yaratish:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🗄️ 6. Django Setup

### 6.1. Migratsiyalarni Bajarish

```bash
python manage.py migrate
```

### 6.2. Superuser Yaratish (ixtiyoriy)

```bash
python manage.py createsuperuser
```

### 6.3. Static Files To'plash (production uchun)

```bash
python manage.py collectstatic --noinput
```

## 🚀 7. Serverni Ishga Tushirish

### Development

```bash
python manage.py runserver
```

Server manzili: `http://127.0.0.1:8000`

### Production (Gunicorn)

```bash
pip install gunicorn

gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## 🧪 8. Birinchi Test

### 8.1. Health Check

Browser'da ochish: `http://localhost:8000/admin/`

### 8.2. To'lov Havolasini Yaratish

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/payments/create-link/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"order_id": "ORD-TEST-001"}'
```

**Expected Response:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.test.paycom.uz/...",
  "order_id": "ORD-TEST-001",
  "amount": 50000
}
```

### 8.3. Webhook Test

1. [TESTING_EXAMPLES.md](TESTING_EXAMPLES.md) faylini ochish
2. CheckPerformTransaction misolini ishga tushiring
3. Firestore'da o'zgarishlarni kuzating

## 🔧 9. Troubleshooting

### Xato: "ModuleNotFoundError: No module named 'decouple'"

```bash
pip install python-decouple
```

### Xato: "Could not find credentials"

Firebase service account faylini tekshiring:
```bash
# Fayl mavjudligini tekshirish
dir secrets\firebase-service-account.json  # Windows
ls secrets/firebase-service-account.json   # Linux/Mac
```

### Xato: "PAYME_KEY is not configured"

`.env` faylini tekshiring va `PAYME_KEY` qo'shilganligiga ishonch hosil qiling.

### Port band bo'lsa

```bash
# Boshqa portda ishga tushirish
python manage.py runserver 8001
```

### Django migration xatolari

```bash
# Barcha migratsiyalarni reset qilish (development uchun)
python manage.py migrate --run-syncdb
```

## 🌐 10. Local Testni Public Qilish (ngrok)

Payme webhook'larini local'da test qilish uchun:

### ngrok o'rnatish

1. [ngrok.com](https://ngrok.com/)ga ro'yxatdan o'ting
2. ngrok'ni yuklab oling
3. Authtoken'ni sozlang

### Serverni expose qilish

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: ngrok
ngrok http 8000
```

ngrok sizga public URL beradi (masalan: `https://abc123.ngrok.io`)

### Payme'da Webhook URL'ni yangilash

Payme Cabinet → Settings → Endpoints:
```
https://abc123.ngrok.io/api/payments/webhook/
```

## 📊 11. Logging Sozlash

`core/settings.py`ga qo'shing:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'payme.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

Log faylni ko'rish:
```bash
# Windows
type payme.log

# Linux/Mac
tail -f payme.log
```

## ✅ 12. Final Checklist

O'rnatish to'g'ri bajarilganligini tekshiring:

- [ ] Python 3.9+ o'rnatilgan
- [ ] Virtual environment faollashtirilgan
- [ ] Barcha dependencies o'rnatilgan (`pip list`)
- [ ] Firebase loyihasi yaratilgan
- [ ] Firestore database ishga tushirilgan
- [ ] Service account JSON fayli `secrets/` papkada
- [ ] Test order Firestore'da yaratilgan
- [ ] Payme akkaunt yaratilgan va tasdiqlanган
- [ ] PAYME_MERCHANT_ID va PAYME_KEY olingan
- [ ] `.env` fayli to'ldirilgan
- [ ] Django server ishga tushadi (`python manage.py runserver`)
- [ ] `/api/payments/create-link/` endpoint ishlaydi
- [ ] Webhook endpoint authentication ishlaydi

## 🎉 Tayyor!

Endi to'liq test qilish uchun [TESTING_EXAMPLES.md](TESTING_EXAMPLES.md) faylini o'qing.

Production'ga deploy qilish uchun [PAYME_INTEGRATION_GUIDE.md](PAYME_INTEGRATION_GUIDE.md) faylining "Production Deploy" bo'limini o'qing.

---

**Savollar uchun:** [Issues](https://github.com/your-repo/issues) ochish yoki support@yourcompany.com ga yozing.
