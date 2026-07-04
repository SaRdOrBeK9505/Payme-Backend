# Swagger/OpenAPI Dokumentatsiya Qo'llanmasi

Bu qo'llanmada Payme Backend API'ning Swagger/OpenAPI dokumentatsiyasidan qanday foydalanish haqida ma'lumot berilgan.

## 📚 Swagger UI Kirish

### Development (Local)

Serverni ishga tushiring:
```bash
python manage.py runserver
```

Keyin brauzerda quyidagi URL'lardan birini oching:

#### 1. Swagger UI (Interactive)
```
http://localhost:8000/api/docs/
```
- ✅ Interaktiv API dokumentatsiya
- ✅ "Try it out" funksiyasi - API'ni to'g'ridan-to'g'ri test qilish
- ✅ Request/Response misollar
- ✅ Schema validatsiya

#### 2. ReDoc (Alternative)
```
http://localhost:8000/api/redoc/
```
- ✅ Chiroyliroq dizayn
- ✅ Yaxshi struktura
- ❌ Interaktiv emas (faqat o'qish)

#### 3. OpenAPI Schema (Raw JSON)
```
http://localhost:8000/api/schema/
```
- OpenAPI 3.0 schema JSON format
- API client'larni generate qilish uchun

### Production

Production URL'ni o'zingizga moslashtiring:
```
https://api.yourcompany.com/api/docs/
https://api.yourcompany.com/api/redoc/
https://api.yourcompany.com/api/schema/
```

---

## 🎯 Swagger UI Xususiyatlari

### 1. API Endpoints Ko'rish

Swagger UI ochilganda, 2 ta asosiy tag ko'rasiz:

#### 📦 Payments
- `POST /api/payments/create-link/` - To'lov havolasini yaratish

#### 🔗 Payme Webhook
- `POST /api/payments/webhook/` - Payme Merchant API webhook

### 2. Endpoint'ni Ochish

Har bir endpoint'ni bosganingizda quyidagilarni ko'rasiz:
- **Description** - Batafsil tavsif
- **Parameters** - Request parametrlari
- **Request Body** - Request body schema
- **Responses** - Mumkin bo'lgan javoblar
- **Examples** - Request va response misollari

### 3. "Try it out" - API'ni Test Qilish

#### CreatePaymentLink Test

1. `POST /api/payments/create-link/` endpoint'ni oching
2. "Try it out" tugmasini bosing
3. Request body'ni to'ldiring:
   ```json
   {
     "order_id": "ORD-TEST-001"
   }
   ```
4. "Execute" tugmasini bosing
5. Response'ni ko'ring:
   ```json
   {
     "success": true,
     "checkout_url": "https://checkout.test.paycom.uz/...",
     "order_id": "ORD-TEST-001",
     "amount": 50000,
     "amount_tiyin": 5000000
   }
   ```

#### Payme Webhook Test

1. `POST /api/payments/webhook/` endpoint'ni oching
2. "Try it out" tugmasini bosing
3. **Authorization header'ni qo'shing:**
   - "Authorize" tugmasini bosing (yuqori o'ng burchakda 🔓)
   - Basic Auth: `Paycom` / `your_payme_key`
   - "Authorize" bosing
4. Request body'ni to'ldiring (CheckPerformTransaction):
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
5. "Execute" tugmasini bosing
6. Response'ni ko'ring

---

## 📖 API Endpoints Batafsil

### 1. POST /api/payments/create-link/

**Maqsad:** Payme checkout havolasini yaratish

**Request:**
```json
{
  "order_id": "ORD-95612789"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "checkout_url": "https://checkout.test.paycom.uz/eyJ...",
  "order_id": "ORD-95612789",
  "amount": 172000,
  "amount_tiyin": 17200000
}
```

**Error Responses:**

**404 - Order Not Found:**
```json
{
  "success": false,
  "error": "Order not found"
}
```

**400 - Order Already Paid:**
```json
{
  "success": false,
  "error": "Order already paid"
}
```

**400 - Order Cancelled:**
```json
{
  "success": false,
  "error": "Order is cancelled"
}
```

### 2. POST /api/payments/webhook/

**Maqsad:** Payme Merchant API JSON-RPC 2.0 webhook

**Authentication:** Basic Auth (Paycom:KEY)

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "MethodName",
  "params": {...}
}
```

**Metodlar:**

#### CheckPerformTransaction
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 17200000,
    "account": {"order_id": "ORD-95612789"}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"allow": true}
}
```

#### CreateTransaction
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "CreateTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11",
    "time": 1675868094123,
    "amount": 17200000,
    "account": {"order_id": "ORD-95612789"}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "create_time": 1675868094123,
    "transaction": "63e31fba6c668e0419b56e11",
    "state": 1
  }
}
```

#### PerformTransaction
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "PerformTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "perform_time": 1675868194123,
    "state": 2
  }
}
```

#### CancelTransaction
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "CancelTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11",
    "reason": 2
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "cancel_time": 1675868294123,
    "state": -1
  }
}
```

#### CheckTransaction
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "CheckTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "create_time": 1675868094123,
    "perform_time": 1675868194123,
    "cancel_time": 0,
    "transaction": "63e31fba6c668e0419b56e11",
    "state": 2,
    "reason": null
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -31050,
    "message": "Order not found",
    "data": "Order not found"
  }
}
```

---

## 🔐 Authentication

### Payme Webhook Authentication

Swagger UI'da "Authorize" tugmasi orqali:

1. Swagger UI'ni oching
2. Yuqori o'ng burchakdagi 🔓 "Authorize" tugmasini bosing
3. **httpBasic (http, Basic)** bo'limiga quyidagilarni kiriting:
   - **Username:** `Paycom`
   - **Password:** `your_payme_key_from_env`
4. "Authorize" tugmasini bosing
5. Oynani yoping

Endi barcha webhook so'rovlar avtomatik ravishda Authorization header bilan yuboriladi.

**Manual header (agar kerak bo'lsa):**
```
Authorization: Basic base64(Paycom:your_payme_key)
```

---

## 🛠️ OpenAPI Schema Download

### JSON Format

```bash
curl http://localhost:8000/api/schema/ -o openapi.json
```

### YAML Format

```bash
curl http://localhost:8000/api/schema/?format=yaml -o openapi.yaml
```

### Schema'dan Client Code Generate Qilish

#### Python Client
```bash
# openapi-generator-cli o'rnatish
npm install -g @openapitools/openapi-generator-cli

# Python client generate qilish
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./payme-python-client
```

#### JavaScript/TypeScript Client
```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o ./payme-ts-client
```

#### Java Client
```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g java \
  -o ./payme-java-client
```

---

## 📱 Postman Collection

### OpenAPI'dan Postman Collection Yaratish

1. Postman'ni oching
2. "Import" tugmasini bosing
3. "Link" tab'ini tanlang
4. URL kiriting: `http://localhost:8000/api/schema/`
5. "Continue" → "Import"

Yoki OpenAPI file'ni yuklab oling va import qiling.

---

## 🎨 Swagger UI Customization

### Logo va Branding

`core/settings.py`da `SPECTACULAR_SETTINGS` ni tahrirlang:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Payme Backend API',
    'DESCRIPTION': 'Your custom description...',
    'VERSION': '1.0.0',
    
    # Custom logo
    'SWAGGER_UI_SETTINGS': {
        'docExpansion': 'none',  # API'larni default yopiq ko'rsatish
        'filter': True,  # Search bar
    },
    
    # Custom CSS/JS
    'SWAGGER_UI_DIST': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/',
}
```

### Dark Mode

Swagger UI'da yuqori o'ng burchakda tema switcher bor.

---

## 🧪 Swagger bilan Testing Best Practices

### 1. Test Orderini Yaratish

Swagger'da test qilishdan avval, Firestore'da test order yarating:

**Firestore Console → orders collection:**
```json
{
  "orderId": "ORD-SWAGGER-TEST",
  "status": "pending",
  "total": 10000,
  "items": [],
  ...
}
```

### 2. To'lov Havolasini Olish

Swagger UI → `POST /api/payments/create-link/`:
```json
{
  "order_id": "ORD-SWAGGER-TEST"
}
```

### 3. Webhook'ni Test Qilish

**Step 1:** Authorize qiling (Paycom / your_key)

**Step 2:** CheckPerformTransaction:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 1000000,
    "account": {"order_id": "ORD-SWAGGER-TEST"}
  }
}
```

**Step 3:** CreateTransaction:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "CreateTransaction",
  "params": {
    "id": "swagger_test_trans_001",
    "time": 1700000000000,
    "amount": 1000000,
    "account": {"order_id": "ORD-SWAGGER-TEST"}
  }
}
```

**Step 4:** CheckTransaction:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "CheckTransaction",
  "params": {
    "id": "swagger_test_trans_001"
  }
}
```

---

## 🔍 Swagger UI Troubleshooting

### Muammo: Swagger UI ochilmaydi

**Yechim:**
```bash
# drf-spectacular o'rnatilganligini tekshiring
pip list | grep spectacular

# Agar yo'q bo'lsa, o'rnating
pip install drf-spectacular

# INSTALLED_APPS'da borligini tekshiring
# settings.py → INSTALLED_APPS → 'drf_spectacular'
```

### Muammo: Authorization ishlamaydi

**Yechim:**
1. Swagger UI'da "Authorize" qilganingizga ishonch hosil qiling
2. Username: `Paycom` (katta harf bilan)
3. Password: `.env` fayldagi `PAYME_KEY` qiymati
4. Browser console'da xatolarni tekshiring (F12)

### Muammo: "Try it out" 500 error qaytaradi

**Yechim:**
1. Django server loglarini tekshiring
2. Firestore'da test order mavjudligini tekshiring
3. Firebase credentials to'g'riligini tekshiring

### Muammo: CORS xatosi (Browser console'da)

**Yechim:**
```bash
pip install django-cors-headers
```

`settings.py`:
```python
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend.com",
]
```

---

## 📚 Qo'shimcha Resurslar

### DRF Spectacular Documentation
- [Official Docs](https://drf-spectacular.readthedocs.io/)
- [GitHub](https://github.com/tfranzel/drf-spectacular)

### OpenAPI Specification
- [OpenAPI 3.0 Spec](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/)

### Swagger UI
- [Swagger UI Docs](https://swagger.io/tools/swagger-ui/)
- [Try Swagger](https://petstore.swagger.io/)

---

## ✅ Swagger Checklist

Setup:
- [x] drf-spectacular o'rnatilgan
- [x] INSTALLED_APPS'da qo'shilgan
- [x] REST_FRAMEWORK settings sozlangan
- [x] SPECTACULAR_SETTINGS konfiguratsiya qilingan
- [x] URL'lar qo'shilgan (schema, docs, redoc)

Testing:
- [x] Swagger UI ochiladi (`/api/docs/`)
- [x] ReDoc ochiladi (`/api/redoc/`)
- [x] OpenAPI schema yuklab olinadi (`/api/schema/`)
- [x] "Try it out" funksiyasi ishlaydi
- [x] Authentication ishlaydi (Payme webhook uchun)

Documentation:
- [x] Har bir endpoint tavsifi yozilgan
- [x] Request/Response examples qo'shilgan
- [x] Authentication requirements ko'rsatilgan
- [x] Error responses hujjatlashtirilgan

---

**Swagger UI'dan foydalanib, API'ni test qiling va development jarayonini tezlashtiring! 🚀**
