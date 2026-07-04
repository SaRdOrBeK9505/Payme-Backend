# ✅ Payme Backend - Final Tekshiruv Checklist

Bu checklist loyihani to'liq tekshirish uchun. Har bir qismni tekshiring va ✅ yoki ❌ belgilang.

---

## 🔧 1. Environment Setup

### Python va Virtual Environment
```bash
# Python versiyasini tekshiring (3.9+ bo'lishi kerak)
python --version

# Virtual environment faollashtirilganmi?
# Windows:
venv\Scripts\activate
# Output: (venv) C:\...\payme_backend>
```

- [ ] Python 3.9+ o'rnatilgan
- [ ] Virtual environment yaratilgan (`venv/` papka bor)
- [ ] Virtual environment faollashtirilgan

---

## 📦 2. Dependencies (Paketlar)

```bash
# Barcha paketlarni tekshiring
pip list
```

### Asosiy Paketlar:

- [ ] **Django** (4.2+) - `pip show Django`
- [ ] **djangorestframework** (3.14+) - `pip show djangorestframework`
- [ ] **drf-spectacular** (0.27+) - `pip show drf-spectacular`
- [ ] **firebase-admin** (6.2+) - `pip show firebase-admin`
- [ ] **google-cloud-firestore** (2.11+) - `pip show google-cloud-firestore`
- [ ] **python-decouple** (3.8+) - `pip show python-decouple`

### Tekshirish:
```bash
pip install -r requirements.txt
```

Agar xato bo'lsa - paketlar to'liq o'rnatilmagan.

---

## 🔐 3. Environment Variables (.env)

### Fayl mavjudmi?
```bash
# Windows
type .env

# PowerShell
Get-Content .env
```

### Kerakli o'zgaruvchilar:

```env
SECRET_KEY=...                    # Django secret key
DEBUG=True                         # Development uchun True
ALLOWED_HOSTS=*                    # Yoki localhost,127.0.0.1

# Payme Configuration
PAYME_MERCHANT_ID=...             # ❗ MAJBURIY - Payme kabinentdan
PAYME_KEY=...                      # ❗ MAJBURIY - Payme secret key
PAYME_ACCOUNT_FIELD=order_id       # Default value
PAYME_ALLOWED_IPS=                 # Test uchun bo'sh qoldiring
```

### Tekshirish:
- [ ] `.env` fayl mavjud
- [ ] `PAYME_MERCHANT_ID` to'ldirilgan (bo'sh emas)
- [ ] `PAYME_KEY` to'ldirilgan (bo'sh emas)
- [ ] `SECRET_KEY` mavjud
- [ ] `DEBUG=True` (development uchun)

---

## 🔥 4. Firebase Setup

### 4.1. Service Account File

```bash
# Fayl mavjudligini tekshiring
# Windows
dir secrets\firebase-service-account.json

# PowerShell
Test-Path secrets\firebase-service-account.json
# Output: True (bo'lishi kerak)
```

- [ ] `secrets/` papka mavjud
- [ ] `secrets/firebase-service-account.json` fayl mavjud
- [ ] JSON fayl to'g'ri formatda (Firebase Console'dan yuklab olingan)

### 4.2. Firebase Connection Test

```bash
python quick_start.py
```

**Expected Output:**
```
🚀 Payme Backend - Quick Start Test
...
Environment.................... ✅ PASSED
Firebase....................... ✅ PASSED
```

- [ ] Firebase connection test muvaffaqiyatli

---

## 🗄️ 5. Firestore Database

### Firebase Console'da:

1. [Firebase Console](https://console.firebase.google.com/) ga kiring
2. Loyihangizni tanlang
3. **Firestore Database** bo'limiga o'ting

### Tekshirish:

- [ ] Firestore Database yaratilgan
- [ ] Database location: `europe-west3` (yoki boshqa region)
- [ ] `orders` collection mavjud (yoki yarating)
- [ ] Kamida 1 ta test order yaratilgan

### Test Order Yaratish:

**Firestore Console → orders collection → Add document:**

```
Document ID: ORD-TEST-001

Fields:
  orderId: "ORD-TEST-001" (string)
  status: "pending" (string)
  total: 50000 (number)
  totalItems: 1 (number)
  address: "Test address" (string)
  phone: "+998901234567" (string)
  region: "Toshkent" (string)
  payment: "Payme" (string)
  delivery: "Kuryer" (string)
  items: [] (array)
  createdAt: 1700000000000 (number)
```

- [ ] Test order yaratilgan

---

## 🗃️ 6. Django Database (SQLite)

```bash
# Migratsiyalarni bajarish
python manage.py migrate

# Expected Output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions
# Running migrations:
#   No migrations to apply. (agar allaqachon bajarilgan bo'lsa)
```

- [ ] `db.sqlite3` fayl yaratilgan
- [ ] Migratsiyalar muvaffaqiyatli

---

## 🚀 7. Django Server

### Server ishga tushirish:

```bash
python manage.py runserver
```

**Expected Output:**
```
Watching for file changes with StatReloader
Performing system checks...
System check identified no issues (0 silenced).
July 03, 2026 - 23:11:39
Django version 5.1.4, using settings 'core.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

- [ ] Server ishga tushdi (xatosiz)
- [ ] URL: http://127.0.0.1:8000/

---

## 📖 8. Swagger UI

### Server ishlayotgan holatda:

**Browser'da ochish:**
```
http://localhost:8000/api/docs/
```

### Ko'rinishi:

- [ ] Swagger UI ochildi
- [ ] "Payme Backend API v1.0.0" title ko'rinadi
- [ ] 2 ta tag ko'rinadi: **Payments** va **Payme Webhook**
- [ ] Endpoint'lar ro'yxati ko'rinadi

### Endpoint'lar:

**Payments Tag:**
- [ ] `POST /api/payments/create-link/` - Ko'rinadi

**Payme Webhook Tag:**
- [ ] `POST /api/payments/webhook/` - Ko'rinadi

---

## 🧪 9. API Testing (Swagger UI orqali)

### Test 1: Create Payment Link

1. Swagger UI → `POST /api/payments/create-link/`
2. **"Try it out"** tugmasi
3. Request body:
   ```json
   {
     "order_id": "ORD-TEST-001"
   }
   ```
4. **"Execute"**

**Expected Response (200):**
```json
{
  "success": true,
  "checkout_url": "https://checkout.test.paycom.uz/...",
  "order_id": "ORD-TEST-001",
  "amount": 50000,
  "amount_tiyin": 5000000
}
```

- [ ] Status Code: 200
- [ ] Response success: true
- [ ] checkout_url mavjud

### Test 2: Payme Webhook (Basic)

**2.1. Authorization:**
1. Yuqori o'ng burchakda **🔓 "Authorize"** tugmasini bosing
2. **Username:** `Paycom`
3. **Password:** `.env` dagi `PAYME_KEY` ni kiriting
4. **"Authorize"** → **"Close"**

- [ ] Authorization muvaffaqiyatli

**2.2. CheckPerformTransaction:**
1. `POST /api/payments/webhook/` ni oching
2. **"Try it out"**
3. Request body:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "CheckPerformTransaction",
     "params": {
       "amount": 5000000,
       "account": {
         "order_id": "ORD-TEST-001"
       }
     }
   }
   ```
4. **"Execute"**

**Expected Response (200):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "allow": true
  }
}
```

- [ ] Status Code: 200
- [ ] result.allow: true

---

## 🔒 10. Authentication Test

### Test: Webhook Without Auth

Swagger UI → `POST /api/payments/webhook/`:

1. **Logout qiling** (Authorize panelida "Logout")
2. So'rov yuboring

**Expected Response (401 yoki 403):**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32504,
    "message": "Access denied",
    ...
  }
}
```

- [ ] Auth bo'lmasa - xato qaytaradi

---

## 📁 11. Fayl Strukturasi

```bash
# Barcha fayllarni tekshirish
dir /b
```

### Root Files:

- [ ] `.env` - Environment variables
- [ ] `.gitignore` - Git ignore rules
- [ ] `manage.py` - Django management
- [ ] `requirements.txt` - Dependencies
- [ ] `quick_start.py` - Test script
- [ ] `LICENSE` - MIT License
- [ ] `README.md` - Main docs
- [ ] `CHANGELOG.md` - Version history
- [ ] `ARCHITECTURE.md` - Architecture docs
- [ ] `PAYME_INTEGRATION_GUIDE.md` - Integration guide
- [ ] `SETUP_GUIDE.md` - Setup instructions
- [ ] `SWAGGER_GUIDE.md` - Swagger documentation
- [ ] `SWAGGER_QUICK_START.md` - Quick Swagger guide
- [ ] `TESTING_EXAMPLES.md` - Test examples
- [ ] `PROJECT_SUMMARY.md` - Project summary
- [ ] `FINAL_CHECKLIST.md` - This file

### Directories:

- [ ] `core/` - Django project settings
- [ ] `payments/` - Payments app
- [ ] `secrets/` - Firebase credentials
- [ ] `venv/` - Virtual environment

---

## 💻 12. Payments App Files

```bash
dir payments
```

- [ ] `__init__.py`
- [ ] `admin.py`
- [ ] `apps.py`
- [ ] `authentication.py` - Auth logic (190+ lines)
- [ ] `constants.py` - Constants (350+ lines)
- [ ] `models.py` - (Bo'sh - Firestore ishlatiladi)
- [ ] `serializers.py` - DRF serializers
- [ ] `services.py` - Business logic (300+ lines)
- [ ] `tests.py` - Unit tests (400+ lines)
- [ ] `urls.py` - URL routing
- [ ] `views.py` - API views (650+ lines)
- [ ] `migrations/` - Django migrations

---

## 🧪 13. Unit Tests

```bash
python manage.py test payments
```

**Expected Output:**
```
Creating test database...
.................
----------------------------------------------------------------------
Ran 15 tests in 0.XXXs

OK
```

- [ ] Barcha testlar muvaffaqiyatli (OK)
- [ ] Xatolar yo'q

---

## 🔍 14. Quick Start Test Script

```bash
python quick_start.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════╗
║  🚀 Payme Backend - Quick Start Test                ║
╚══════════════════════════════════════════════════════╝

1. Environment Variables Tekshiruvi
✅ PAYME_MERCHANT_ID: ********** (configured)
✅ PAYME_KEY: ********** (configured)
...

Jami: 5/5 test muvaffaqiyatli
✅ 🎉 Barcha testlar muvaffaqiyatli! Loyiha tayyor!
```

- [ ] Barcha 5 test PASSED
- [ ] Xatolar yo'q

---

## 📊 15. Code Quality Checks

### Syntax Check:

```bash
python -m py_compile payments\constants.py
python -m py_compile payments\authentication.py
python -m py_compile payments\services.py
python -m py_compile payments\views.py
```

- [ ] Syntax xatolari yo'q

### Import Check:

```bash
python -c "from payments import views, services, constants"
```

- [ ] Import xatolari yo'q

---

## 🌐 16. API Endpoints (Manual Test)

### PowerShell orqali:

**Test 1: Health Check**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/admin/"
# Output: StatusCode: 200
```

- [ ] Admin panel ochiladi

**Test 2: Create Payment Link**
```powershell
$body = '{"order_id": "ORD-TEST-001"}' | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/payments/create-link/" -Method POST -ContentType "application/json" -Body $body
```

- [ ] Response success: true

---

## 📚 17. Documentation Review

### Har bir hujjat mavjudmi?

- [ ] README.md (yangilangan, Swagger URL'lar bor)
- [ ] SETUP_GUIDE.md (400+ lines)
- [ ] PAYME_INTEGRATION_GUIDE.md (600+ lines)
- [ ] TESTING_EXAMPLES.md (500+ lines)
- [ ] SWAGGER_GUIDE.md (600+ lines)
- [ ] SWAGGER_QUICK_START.md (50+ lines)
- [ ] ARCHITECTURE.md (400+ lines)
- [ ] PROJECT_SUMMARY.md (300+ lines)
- [ ] CHANGELOG.md (200+ lines)

---

## 🔐 18. Security Checks

### .env File:

- [ ] `.env` git'ga tushmaydi (`.gitignore` da bor)
- [ ] `secrets/` papka git'ga tushmaydi

### Check:
```bash
type .gitignore | findstr ".env"
type .gitignore | findstr "secrets"
```

- [ ] Ikkalasi ham `.gitignore` da

---

## 🎯 19. Payme Configuration

### Payme Merchant Cabinet:

1. [Payme Merchant](https://merchant.payme.uz/) ga kiring
2. Settings → API

**Tekshirish:**

- [ ] Merchant ID olingan
- [ ] Secret Key olingan
- [ ] `.env` faylda to'ldirilgan

---

## 🚀 20. Production Readiness

### Hozirgi Status:

- [ ] Development environment ishlaydi
- [ ] Barcha testlar o'tadi
- [ ] Swagger docs ochiladi
- [ ] API endpoints ishlaydi
- [ ] Authentication ishlaydi
- [ ] Firebase connection ishlaydi

### Production uchun kerak:

- [ ] `.env` faylida production qiymatlar
  - `DEBUG=False`
  - `PAYME_ALLOWED_IPS=185.178.51.131,...` (to'ldirish)
- [ ] Nginx konfiguratsiyasi
- [ ] Gunicorn setup
- [ ] SSL sertifikati
- [ ] Payme Cabinet'da webhook URL sozlash

---

## ✅ FINAL SCORE

### Minimal Requirements (Development):

**Majburiy (10/10):**
1. ✅ Python 3.9+ o'rnatilgan
2. ✅ Dependencies o'rnatilgan
3. ✅ .env fayl to'ldirilgan (PAYME_MERCHANT_ID, PAYME_KEY)
4. ✅ Firebase service account fayl mavjud
5. ✅ Test order Firestore'da yaratilgan
6. ✅ Django server ishga tushadi
7. ✅ Swagger UI ochiladi
8. ✅ Create payment link API ishlaydi
9. ✅ Webhook API ishlaydi
10. ✅ Quick start test muvaffaqiyatli

**Agar 10/10 bo'lsa - Loyiha tayyor! 🎉**

---

## 🐛 Troubleshooting

### Agar muammo bo'lsa:

**1. Server ishga tushmaydi:**
```bash
# Loglarni tekshiring
python manage.py runserver
# Xatolarni o'qing va SETUP_GUIDE.md → Troubleshooting bo'limiga qarang
```

**2. Firebase connection xatosi:**
```bash
# Service account file to'g'riligini tekshiring
python -c "from core.firebase_config import db; print(db)"
```

**3. Swagger UI ochilmaydi:**
```bash
# drf-spectacular o'rnatilganini tekshiring
pip show drf-spectacular
```

**4. API 500 error:**
```bash
# Django loglarni tekshiring
# Browser console'ni tekshiring (F12)
```

---

## 📞 Yordam

Agar biror narsa ishlamasa:

1. **SETUP_GUIDE.md** → Troubleshooting
2. **quick_start.py** - Diagnostics
3. **TESTING_EXAMPLES.md** - Test examples
4. Django server loglarini o'qing

---

## 🎉 SUCCESS!

Agar barcha checklistlar ✅ bo'lsa:

**TABRIKLAYMIZ! 🎊**

Loyihangiz to'liq tayyor va production-ready!

**Keyingi qadamlar:**
1. Swagger UI'da to'liq test qiling
2. Real Payme to'lovlarini test muhitda sinab ko'ring
3. Production deploy qilish uchun PAYME_INTEGRATION_GUIDE.md o'qing

---

**Muvaffaqiyatlar! 🚀**
