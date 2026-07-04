# Swagger UI - Tezkor Boshlash

## 🎯 Swagger UI'ga Kirish

1. **Serverni ishga tushiring:**
   ```bash
   python manage.py runserver
   ```

2. **Brauzerda oching:**
   ```
   http://localhost:8000/api/docs/
   ```

3. **Swagger UI ochiladi!** 🎉

---

## ⚡ 5 Daqiqada Test Qilish

### 1️⃣ To'lov Havolasini Yaratish

1. Swagger UI'da `POST /api/payments/create-link/` ni oching
2. **"Try it out"** tugmasini bosing
3. Request body'ga kiriting:
   ```json
   {
     "order_id": "ORD-TEST-001"
   }
   ```
4. **"Execute"** bosing
5. Response'ni ko'ring! ✅

### 2️⃣ Payme Webhook'ni Test Qilish

1. Yuqori o'ng burchakda **🔓 "Authorize"** tugmasini bosing
2. **Username:** `Paycom`
3. **Password:** `.env` fayldagi `PAYME_KEY` qiymatini kiriting
4. **"Authorize"** → **"Close"**

5. `POST /api/payments/webhook/` ni oching
6. **"Try it out"** tugmasini bosing
7. Request body'ga kiriting:
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
8. **"Execute"** bosing
9. Response'ni ko'ring! ✅

---

## 📱 URL'lar

| Sahifa | URL | Tavsif |
|--------|-----|--------|
| **Swagger UI** | http://localhost:8000/api/docs/ | Interaktiv API docs |
| **ReDoc** | http://localhost:8000/api/redoc/ | Chiroyliroq docs |
| **OpenAPI Schema** | http://localhost:8000/api/schema/ | JSON schema |

---

## 💡 Maslahatlar

### ✅ Swagger UI Xususiyatlari

- 🔍 **Search Bar** - Endpoint'larni qidirish
- 🎨 **Dark Mode** - Yuqori o'ng burchakda
- 📋 **Copy** - Response'larni nusxalash
- 🔄 **History** - So'rovlar tarixi

### 🚀 Tezkor Test

**Test Order Yaratish (Firestore):**
```json
{
  "orderId": "ORD-TEST-001",
  "status": "pending",
  "total": 50000,
  "items": []
}
```

**To'liq test scenariylari:**
- [TESTING_EXAMPLES.md](TESTING_EXAMPLES.md)
- [SWAGGER_GUIDE.md](SWAGGER_GUIDE.md)

---

**Swagger UI'dan rohatlaning! 🎉**
