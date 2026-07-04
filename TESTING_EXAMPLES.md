# Payme Integration Testing Examples

Bu faylda Payme integratsiyasini test qilish uchun amaliy misollar keltirilgan.

## 📋 Test Qilish Uchun Tayyorgarlik

### 1. Firestore'da Test Order Yaratish

Firestore Console'da `orders` collection'ida quyidagi order'ni yarating:

**Document ID:** `ORD-TEST-001`

**Document Data:**
```json
{
  "orderId": "ORD-TEST-001",
  "status": "pending",
  "total": 50000,
  "totalItems": 2,
  "address": "Test address, Tashkent",
  "phone": "+998901234567",
  "region": "Toshkent",
  "payment": "Payme",
  "delivery": "Kuryer",
  "comment": "Test order for Payme integration",
  "items": [
    {
      "id": "item1",
      "title": "Test Product 1",
      "price": 25000,
      "quantity": 1
    },
    {
      "id": "item2",
      "title": "Test Product 2",
      "price": 25000,
      "quantity": 1
    }
  ],
  "createdAt": 1700000000000,
  "user": null
}
```

### 2. .env Faylini To'ldirish

```env
PAYME_MERCHANT_ID=your_test_merchant_id
PAYME_KEY=your_test_key
PAYME_ACCOUNT_FIELD=order_id
# Test muhitda IP whitelist'ni bo'sh qoldiring
PAYME_ALLOWED_IPS=
```

### 3. Serverni Ishga Tushirish

```bash
python manage.py runserver
```

---

## 🧪 Test Scenariyalari

### Scenario 1: To'lov Havolasini Yaratish va Muvaffaqiyatli To'lov

#### Step 1: To'lov Havolasini Olish

**cURL (Linux/Mac):**
```bash
curl -X POST http://localhost:8000/api/payments/create-link/ \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-TEST-001"}'
```

**PowerShell (Windows):**
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
  "checkout_url": "https://checkout.test.paycom.uz/eyJt...",
  "order_id": "ORD-TEST-001",
  "amount": 50000,
  "amount_tiyin": 5000000
}
```

#### Step 2: CheckPerformTransaction

Payme bu metoddan avval order validligini tekshiradi.

**cURL:**
```bash
# Avval Basic Auth header'ni yaratish
AUTH=$(echo -n "Paycom:YOUR_PAYME_KEY" | base64)

curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 5000000,
      "account": {
        "order_id": "ORD-TEST-001"
      }
    }
  }'
```

**PowerShell:**
```powershell
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("Paycom:YOUR_PAYME_KEY"))

$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "CheckPerformTransaction"
    params = @{
        amount = 5000000
        account = @{
            order_id = "ORD-TEST-001"
        }
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/payments/webhook/" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Basic $auth"
  } `
  -Body $body
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "allow": true
  }
}
```

#### Step 3: CreateTransaction

Tranzaksiya yaratish.

**cURL:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "CreateTransaction",
    "params": {
      "id": "63e31fba6c668e0419b56e11",
      "time": 1675868094123,
      "amount": 5000000,
      "account": {
        "order_id": "ORD-TEST-001"
      }
    }
  }'
```

**PowerShell:**
```powershell
$body = @{
    jsonrpc = "2.0"
    id = 2
    method = "CreateTransaction"
    params = @{
        id = "63e31fba6c668e0419b56e11"
        time = 1675868094123
        amount = 5000000
        account = @{
            order_id = "ORD-TEST-001"
        }
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/payments/webhook/" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Basic $auth"
  } `
  -Body $body
```

**Expected Response:**
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

**Firestore'da Tekshirish:**
- `orders/ORD-TEST-001` → status: `processing`
- `transactions/63e31fba6c668e0419b56e11` → state: `1` (created)

#### Step 4: CheckTransaction

Tranzaksiya holatini tekshirish.

**cURL:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "CheckTransaction",
    "params": {
      "id": "63e31fba6c668e0419b56e11"
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "create_time": 1675868094123,
    "perform_time": 0,
    "cancel_time": 0,
    "transaction": "63e31fba6c668e0419b56e11",
    "state": 1,
    "reason": null
  }
}
```

#### Step 5: PerformTransaction

To'lovni tasdiqash (client to'lovni amalga oshirgandan keyin).

**cURL:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "PerformTransaction",
    "params": {
      "id": "63e31fba6c668e0419b56e11"
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "perform_time": 1675868194123,
    "state": 2
  }
}
```

**Firestore'da Tekshirish:**
- `orders/ORD-TEST-001` → status: `paid` ✅
- `transactions/63e31fba6c668e0419b56e11` → state: `2` (completed)

---

### Scenario 2: To'lovni Bekor Qilish (Cancel Before Perform)

Tranzaksiya yaratilgan, lekin hali to'lov amalga oshirilmagan.

#### Step 1-3: Yuqoridagi kabi (CheckPerform → CreateTransaction)

#### Step 4: CancelTransaction

**cURL:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "CancelTransaction",
    "params": {
      "id": "63e31fba6c668e0419b56e11",
      "reason": 1
    }
  }'
```

**Reason Codes:**
- `1` - Client bekor qildi
- `2` - Mahsulot yo'q
- `3` - Texnik xato
- `4` - Timeout
- `5` - Qayta to'lash

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "cancel_time": 1675868294123,
    "state": -1
  }
}
```

**Firestore'da Tekshirish:**
- `orders/ORD-TEST-001` → status: `pending` (qaytdi)
- `transactions/63e31fba6c668e0419b56e11` → state: `-1` (cancelled)

---

### Scenario 3: To'lovni Bekor Qilish (Cancel After Perform)

To'lov amalga oshirilgan, keyin bekor qilingan (refund).

#### Step 1-5: Muvaffaqiyatli to'lov (yuqoridagi Scenario 1)

#### Step 6: CancelTransaction

**cURL:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $AUTH" \
  -d '{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "CancelTransaction",
    "params": {
      "id": "63e31fba6c668e0419b56e11",
      "reason": 5
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "transaction": "63e31fba6c668e0419b56e11",
    "cancel_time": 1675868394123,
    "state": -2
  }
}
```

**Firestore'da Tekshirish:**
- `orders/ORD-TEST-001` → status: `cancelled`
- `transactions/63e31fba6c668e0419b56e11` → state: `-2` (cancelled after complete)

---

### Scenario 4: Xato Holatlar

#### 4.1: Order Topilmadi

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 5000000,
    "account": {
      "order_id": "ORD-NOT-EXIST"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "error": {
    "code": -31050,
    "message": "Order not found",
    "data": "Order not found"
  }
}
```

#### 4.2: Noto'g'ri Summa

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 9999999,
    "account": {
      "order_id": "ORD-TEST-001"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "error": {
    "code": -31001,
    "message": "Incorrect amount",
    "data": "Incorrect amount. Expected: 5000000, got: 9999999"
  }
}
```

#### 4.3: Noto'g'ri Authentication

**Request header'siz yoki noto'g'ri:**
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 9, "method": "CheckTransaction", "params": {"id": "test"}}'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32504,
    "message": "Access denied",
    "data": "Authorization header is missing"
  }
}
```

#### 4.4: Tranzaksiya Topilmadi

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "CheckTransaction",
  "params": {
    "id": "non_existent_transaction"
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "error": {
    "code": -31003,
    "message": "Transaction not found",
    "data": "Transaction not found"
  }
}
```

#### 4.5: Order Allaqachon To'langan

Agar order status = "paid" bo'lsa:

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 5000000,
    "account": {
      "order_id": "ORD-PAID-ORDER"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "error": {
    "code": -31051,
    "message": "Order already paid",
    "data": "Order already paid"
  }
}
```

---

## 🔧 Python Script Bilan Test Qilish

Agar curl o'rniga Python script ishlatmoqchi bo'lsangiz:

```python
# test_payme.py
import requests
import base64
import json

BASE_URL = "http://localhost:8000"
PAYME_KEY = "your_payme_key_here"

# Basic Auth header yaratish
auth_string = f"Paycom:{PAYME_KEY}"
auth_bytes = auth_string.encode('ascii')
auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth_base64}"
}

def test_check_perform_transaction():
    """CheckPerformTransaction test"""
    payload = {
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
    
    response = requests.post(
        f"{BASE_URL}/api/payments/webhook/",
        headers=headers,
        json=payload
    )
    
    print("CheckPerformTransaction Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_create_transaction():
    """CreateTransaction test"""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "CreateTransaction",
        "params": {
            "id": "test_trans_001",
            "time": 1675868094123,
            "amount": 5000000,
            "account": {
                "order_id": "ORD-TEST-001"
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/payments/webhook/",
        headers=headers,
        json=payload
    )
    
    print("CreateTransaction Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_perform_transaction(transaction_id):
    """PerformTransaction test"""
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "PerformTransaction",
        "params": {
            "id": transaction_id
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/payments/webhook/",
        headers=headers,
        json=payload
    )
    
    print("PerformTransaction Response:")
    print(json.dumps(response.json(), indent=2))
    print()

if __name__ == "__main__":
    print("=== Payme Integration Tests ===\n")
    
    # Test 1: CheckPerformTransaction
    test_check_perform_transaction()
    
    # Test 2: CreateTransaction
    test_create_transaction()
    
    # Test 3: PerformTransaction
    test_perform_transaction("test_trans_001")
    
    print("=== Tests Completed ===")
```

**Ishga tushirish:**
```bash
python test_payme.py
```

---

## ✅ Test Checklist

To'liq test qilish uchun quyidagilarni tekshiring:

### API Endpoints
- [ ] `POST /api/payments/create-link/` - muvaffaqiyatli
- [ ] `POST /api/payments/create-link/` - order topilmasa
- [ ] `POST /api/payments/create-link/` - order allaqachon to'langan

### Webhook Methods
- [ ] `CheckPerformTransaction` - muvaffaqiyatli
- [ ] `CheckPerformTransaction` - noto'g'ri summa
- [ ] `CheckPerformTransaction` - order topilmadi
- [ ] `CreateTransaction` - yangi tranzaksiya
- [ ] `CreateTransaction` - mavjud tranzaksiya (idempotency)
- [ ] `PerformTransaction` - muvaffaqiyatli
- [ ] `PerformTransaction` - tranzaksiya topilmadi
- [ ] `CancelTransaction` - perform'dan oldin
- [ ] `CancelTransaction` - perform'dan keyin
- [ ] `CheckTransaction` - mavjud tranzaksiya
- [ ] `CheckTransaction` - topilmagan tranzaksiya

### Authentication & Security
- [ ] Basic Auth - to'g'ri credentials
- [ ] Basic Auth - noto'g'ri credentials
- [ ] Basic Auth - header yo'q
- [ ] IP Whitelist - ruxsat etilgan IP
- [ ] IP Whitelist - ruxsat etilmagan IP

### Firestore Integration
- [ ] Order status yangilanishi (pending → processing → paid)
- [ ] Tranzaksiya yaratilishi
- [ ] Tranzaksiya state yangilanishi
- [ ] Cancel qilinganda statusni qaytarish

---

## 🐛 Debugging Tips

### 1. Django Logs Ko'rish

```bash
# Terminal'da serverni ishga tushirganda
python manage.py runserver

# Alohida log faylni ko'rish
tail -f payme.log
```

### 2. Firestore Console'da Real-time Ko'rish

1. [Firebase Console](https://console.firebase.google.com/)ga kiring
2. Firestore Database → Data
3. `orders` va `transactions` collection'larini kuzating

### 3. Request/Response Log Qilish

`payments/views.py`ga qo'shing:

```python
import logging
logger = logging.getLogger(__name__)

def post(self, request):
    logger.info(f"Request: {request.data}")
    # ... existing code
    logger.info(f"Response: {response_data}")
```

---

**Muvaffaqiyatli test qilish! 🚀**
