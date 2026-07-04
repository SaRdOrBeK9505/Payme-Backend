# Payme Merchant API Integratsiya Qo'llanmasi

Bu qo'llanmada Payme to'lov tizimini Django + DRF + Firebase Firestore bilan qanday integratsiya qilish va test qilish usullari keltirilgan.

## 📋 Mundarija

1. [O'rnatish](#o'rnatish)
2. [Konfiguratsiya](#konfiguratsiya)
3. [Arxitektura](#arxitektura)
4. [API Endpointlari](#api-endpointlari)
5. [Test Qilish](#test-qilish)
6. [Production Deploy](#production-deploy)

---

## 🚀 O'rnatish

### 1. Dependencies'ni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. Firebase Service Account sozlash

`secrets/firebase-service-account.json` faylini Payme loyihangizdagi Firebase Service Account kaliti bilan to'ldiring.

### 3. Environment variables sozlash

`.env` faylini tahrirlang:

```env
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Payme konfiguratsiyalari
PAYME_MERCHANT_ID=your_merchant_id_here
PAYME_KEY=your_payme_key_here
PAYME_ACCOUNT_FIELD=order_id

# Payme IP whitelist (production uchun)
PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

**Muhim:** 
- `PAYME_MERCHANT_ID` - Payme kabinentingizdan olinadi
- `PAYME_KEY` - Payme Merchant API kaliti (Secret Key)
- `PAYME_ALLOWED_IPS` - Production'da faqat Payme serverlaridan kelgan so'rovlarni qabul qilish uchun

### 4. Django migratsiyalarini bajarish

```bash
python manage.py migrate
```

### 5. Serverni ishga tushirish

```bash
python manage.py runserver
```

---

## ⚙️ Konfiguratsiya

### Payme Merchant ID va Key olish

1. [Payme Merchant Cabinet](https://merchant.payme.uz/)ga kiring
2. Settings → Merchant API → API Key'ni nusxalang
3. Merchant ID'ni nusxalang

### Firestore Collection Strukturasi

Loyiha quyidagi Firestore collection'laridan foydalanadi:

#### `orders` collection

```javascript
{
  "orderId": "ORD-95612789",
  "status": "pending",  // pending, processing, paid, delivered, cancelled
  "total": 172000,      // so'mda
  "address": "test uchun",
  "phone": "+998 91 171 26 11",
  "region": "Andijon",
  "payment": "Payme (online to'lov)",
  "delivery": "Kuryer (yetkazib berish)",
  "items": [
    {
      "id": "b0LMcepJCCC3NkqkRbtc",
      "title": "SH KE 2161",
      "price": 172000,
      "quantity": 1
    }
  ],
  "createdAt": 1783078660589,
  "updatedAt": 1783078660589
}
```

#### `transactions` collection (avtomatik yaratiladi)

```javascript
{
  "id": "payme_transaction_id",
  "orderId": "ORD-95612789",
  "amount": 17200000,  // tiyinlarda (so'm * 100)
  "state": 1,          // 1: created, 2: completed, -1: cancelled, -2: cancelled_after_complete
  "createTime": 1609459200000,
  "performTime": 1609459800000,
  "cancelTime": null,
  "reason": null,
  "account": {
    "order_id": "ORD-95612789"
  },
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:10:00Z"
}
```

---

## 🏗️ Arxitektura

### Fayllar Strukturasi

```
payments/
├── constants.py         # Payme konstantalari (xato kodlari, metodlar, holatlar)
├── authentication.py    # Basic Auth va IP whitelist tekshiruvlari
├── services.py          # Firestore CRUD logikasi (OrderService, TransactionService)
├── views.py            # API view'lar (CreatePaymentLinkView, PaymeWebhookView)
├── urls.py             # URL routing
└── models.py           # (Bo'sh - Firestore ishlatilmoqda)
```

### Arxitektura Tanlovi: Alohida Transactions Collection

**Nima uchun tranzaksiyalarni alohida collection'da saqlaymiz?**

1. **Scalability:** Orderlar va tranzaksiyalar mustaqil ravishda o'sishi mumkin
2. **Query Performance:** Tranzaksiyalar bo'yicha tez qidiruv (index'lar orqali)
3. **Data Integrity:** Order ma'lumotlari va to'lov tarixi alohida
4. **Audit Trail:** To'lov tarixini to'liq saqlash (qayta urinishlar, bekor qilishlar)
5. **Payme Requirements:** Payme bir order uchun bir nechta tranzaksiya yaratishi mumkin

**Alternativa:** Tranzaksiyalarni order ichida nested document sifatida saqlash mumkin, lekin bu katta orderlar uchun performance muammolariga olib keladi.

---

## 📡 API Endpointlari

### 1. To'lov Havolasini Yaratish

**Endpoint:** `POST /api/payments/create-link/`

**Request:**

```json
{
  "order_id": "ORD-95612789"
}
```

**Response (Success):**

```json
{
  "success": true,
  "checkout_url": "https://checkout.paycom.uz/eyJtIjogInlvdXJfbWVyY2hhbnRfaWQiLCAiYWMiOiB7Im9yZGVyX2lkIjogIk9SRC0xMjM0NSJ9LCAiYSI6IDE3MjAwMDAwfQ==",
  "order_id": "ORD-95612789",
  "amount": 172000,
  "amount_tiyin": 17200000
}
```

**Response (Error):**

```json
{
  "success": false,
  "error": "Order not found"
}
```

**Status Kodlari:**
- `200` - Muvaffaqiyatli
- `400` - Order allaqachon to'langan yoki bekor qilingan
- `404` - Order topilmadi
- `500` - Server xatosi

### 2. Payme Webhook (Merchant API)

**Endpoint:** `POST /api/payments/webhook/`

**Headers:**

```
Authorization: Basic base64(Paycom:YOUR_PAYME_KEY)
Content-Type: application/json
```

Bu endpoint quyidagi metodlarni qo'llab-quvvatlaydi:

#### CheckPerformTransaction

Order to'lov uchun tayyor ekanligini tekshiradi.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 17200000,
    "account": {
      "order_id": "ORD-95612789"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "allow": true
  }
}
```

#### CreateTransaction

Yangi tranzaksiya yaratadi.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CreateTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11",
    "time": 1675868094123,
    "amount": 17200000,
    "account": {
      "order_id": "ORD-95612789"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "create_time": 1675868094123,
    "transaction": "63e31fba6c668e0419b56e11",
    "state": 1
  }
}
```

#### PerformTransaction

Tranzaksiyani tasdiqlab, to'lovni amalga oshiradi.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
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
  "id": 123,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "perform_time": 1675868194123,
    "state": 2
  }
}
```

#### CancelTransaction

Tranzaksiyani bekor qiladi.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CancelTransaction",
  "params": {
    "id": "63e31fba6c668e0419b56e11",
    "reason": 2
  }
}
```

**Cancel Reason Kodlari:**
- `1` - Client tomonidan bekor qilingan
- `2` - Mahsulot/xizmat mavjud emas
- `3` - Texnik xato
- `4` - Timeout
- `5` - Qayta to'lash (refund)

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "cancel_time": 1675868294123,
    "state": -1
  }
}
```

#### CheckTransaction

Tranzaksiya holatini tekshiradi.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 123,
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
  "id": 123,
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

---

## 🧪 Test Qilish

### 1. To'lov Havolasini Test Qilish

```bash
curl -X POST http://localhost:8000/api/payments/create-link/ \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-95612789"}'
```

### 2. CheckPerformTransaction Test

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'Paycom:YOUR_PAYME_KEY' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 17200000,
      "account": {"order_id": "ORD-95612789"}
    }
  }'
```

**Windows PowerShell uchun:**

```powershell
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("Paycom:YOUR_PAYME_KEY"))

Invoke-RestMethod -Uri "http://localhost:8000/api/payments/webhook/" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Basic $auth"
  } `
  -Body '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 17200000,
      "account": {"order_id": "ORD-95612789"}
    }
  }'
```

### 3. CreateTransaction Test

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'Paycom:YOUR_PAYME_KEY' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "CreateTransaction",
    "params": {
      "id": "test_transaction_001",
      "time": 1675868094123,
      "amount": 17200000,
      "account": {"order_id": "ORD-95612789"}
    }
  }'
```

### 4. PerformTransaction Test

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'Paycom:YOUR_PAYME_KEY' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "PerformTransaction",
    "params": {
      "id": "test_transaction_001"
    }
  }'
```

### 5. CheckTransaction Test

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'Paycom:YOUR_PAYME_KEY' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "CheckTransaction",
    "params": {
      "id": "test_transaction_001"
    }
  }'
```

### 6. CancelTransaction Test

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'Paycom:YOUR_PAYME_KEY' | base64)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "CancelTransaction",
    "params": {
      "id": "test_transaction_001",
      "reason": 1
    }
  }'
```

### Test Scenariylari

#### Scenario 1: Muvaffaqiyatli To'lov

1. Order yaratish (Telegram Mini App orqali)
2. `POST /api/payments/create-link/` - havolani olish
3. Foydalanuvchi Payme'da to'lovni amalga oshiradi
4. Payme webhook'larni yuboradi:
   - `CheckPerformTransaction` ✅
   - `CreateTransaction` ✅
   - `PerformTransaction` ✅
5. Order status → `paid`

#### Scenario 2: Bekor Qilingan To'lov

1. Order yaratish
2. To'lov havolasini olish
3. Foydalanuvchi to'lovni boshlaydi
4. `CreateTransaction` ✅
5. Foydalanuvchi to'lovni bekor qiladi
6. `CancelTransaction` ✅
7. Order status → `pending` (qaytadi)

#### Scenario 3: Timeout

1. Order yaratish
2. `CreateTransaction` ✅
3. 12 soat ichida `PerformTransaction` kelmaydi
4. Payme `CancelTransaction` (reason=4) yuboradi ✅
5. Order status → `pending`

---

## 🔒 Xavfsizlik

### 1. Basic Authentication

Barcha webhook so'rovlari quyidagi header bilan kelishi kerak:

```
Authorization: Basic base64(Paycom:YOUR_PAYME_KEY)
```

### 2. IP Whitelist

Production'da faqat Payme serverlaridan kelgan so'rovlarni qabul qilish:

```env
PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

Test muhitda bo'sh qoldiring yoki local IP qo'shing.

### 3. Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Orders - faqat authenticated users
    match /orders/{orderId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
    
    // Transactions - faqat server tomonidan
    match /transactions/{transactionId} {
      allow read: if request.auth != null;
      allow write: if false; // Faqat server SDK orqali
    }
  }
}
```

---

## 🚀 Production Deploy

### 1. Environment Variables

Production `.env` faylini to'ldiring:

```env
SECRET_KEY=production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

PAYME_MERCHANT_ID=production_merchant_id
PAYME_KEY=production_payme_key
PAYME_ACCOUNT_FIELD=order_id
PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

### 2. Static Files

```bash
python manage.py collectstatic --noinput
```

### 3. Gunicorn/uWSGI

```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 4. Nginx Konfiguratsiyasi

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/payments/webhook/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

### 5. Payme Kabinentda Webhook URL'ni sozlash

1. [Payme Merchant Cabinet](https://merchant.payme.uz/)ga kiring
2. Settings → Endpoints
3. Webhook URL: `https://your-domain.com/api/payments/webhook/`
4. Test qiling va saqlang

---

## 📊 Logging va Monitoring

### Django Logging Sozlash

`settings.py`ga qo'shing:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'payme.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
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

### Monitoring Checklist

- [ ] Tranzaksiya yaratilishi
- [ ] To'lov tasdiqlanishi
- [ ] Bekor qilinishlar
- [ ] Xatolar va exception'lar
- [ ] API response time'lari
- [ ] Firestore write/read operations

---

## ❓ Tez-tez So'raladigan Savollar

### Q: Bir order uchun bir nechta tranzaksiya yaratilishi mumkinmi?

**A:** Ha, agar foydalanuvchi to'lovni bir necha marta urinib ko'rsa. Shuning uchun `CreateTransaction`da tranzaksiya mavjudligini tekshiramiz va mavjud bo'lsa, uni qaytaramiz.

### Q: Order statusini qachon `paid` ga o'zgartirish kerak?

**A:** Faqat `PerformTransaction` metodi muvaffaqiyatli bajarilgandan keyin. `CreateTransaction` faqat `processing` statusiga o'tkazadi.

### Q: Timeout necha vaqt?

**A:** Payme 12 soat (43200000 millisekund) kutadi. Agar bu vaqt ichida `PerformTransaction` kelmasa, tranzaksiya avtomatik bekor qilinadi.

### Q: Test muhitda qanday test qilsam bo'ladi?

**A:** Payme test muhiti: `https://checkout.test.paycom.uz/`. Test kartalar:
- Karta: `8600 0000 0000 0000`
- Muddati: `03/99`
- SMS kod: `666666`

### Q: IP whitelist test muhitda ishlaydimi?

**A:** Test muhitda IP whitelist'ni bo'sh qoldiring yoki o'chirib qo'ying. Production'da majburiy.

---

## 📞 Qo'llab-quvvatlash

Agar muammolar yuzaga kelsa:

1. **Payme Documentation:** [payme.uz/docs](https://developer.help.paycom.uz/)
2. **Payme Support:** support@paycom.uz
3. **Firebase Documentation:** [firebase.google.com/docs](https://firebase.google.com/docs/firestore)

---

## 📝 Changelog

### Version 1.0.0 (2024)
- ✅ Payme Merchant API to'liq integratsiyasi
- ✅ Firebase Firestore bilan ishlash
- ✅ Basic Auth va IP whitelist
- ✅ Barcha 5 ta JSON-RPC metod qo'llab-quvvatlash
- ✅ To'liq xato kodlari va validation
- ✅ Production-ready kod

---

**Muvaffaqiyatlar tilaymiz! 🚀**
