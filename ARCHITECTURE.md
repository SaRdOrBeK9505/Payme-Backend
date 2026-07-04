# Payme Integration - Arxitektura Hujjatlari

## 📐 Sistema Arxitekturasi

### High-Level Overview

```
┌─────────────────────┐
│  Telegram Mini App  │
│   (Frontend)        │
└──────────┬──────────┘
           │
           │ HTTP/HTTPS
           ▼
┌─────────────────────────────────────┐
│  Django Backend (To'lov Service)    │
│  ┌───────────────────────────────┐  │
│  │  REST API Endpoints           │  │
│  │  - /api/payments/create-link/ │  │
│  │  - /api/payments/webhook/     │  │
│  └──────────┬────────────────────┘  │
│             │                        │
│  ┌──────────▼────────────────────┐  │
│  │  Business Logic Layer         │  │
│  │  - OrderService               │  │
│  │  - TransactionService         │  │
│  └──────────┬────────────────────┘  │
│             │                        │
│  ┌──────────▼────────────────────┐  │
│  │  Authentication Layer         │  │
│  │  - Basic Auth (Paycom:KEY)    │  │
│  │  - IP Whitelist               │  │
│  └───────────────────────────────┘  │
└────────────┬────────────────────────┘
             │
             │ Firebase Admin SDK
             ▼
    ┌────────────────────┐
    │  Firebase Firestore│
    │  ┌──────────────┐  │
    │  │  orders      │  │
    │  │  collection  │  │
    │  └──────────────┘  │
    │  ┌──────────────┐  │
    │  │ transactions │  │
    │  │  collection  │  │
    │  └──────────────┘  │
    └────────────────────┘
             ▲
             │
             │ Webhook (JSON-RPC 2.0)
             │
    ┌────────┴───────────┐
    │  Payme Merchant    │
    │  API Server        │
    └────────────────────┘
```

## 🗂️ Fayl Strukturasi

```
payme_backend/
│
├── core/                          # Django project settings
│   ├── __init__.py
│   ├── settings.py               # Asosiy konfiguratsiya
│   ├── urls.py                   # Root URL routing
│   ├── wsgi.py                   # WSGI entry point
│   ├── asgi.py                   # ASGI entry point
│   └── firebase_config.py        # Firebase initialization
│
├── payments/                      # Payme app
│   ├── __init__.py
│   ├── constants.py              # Payme konstantalari
│   ├── authentication.py         # Auth va security
│   ├── services.py               # Biznes logika
│   ├── views.py                  # API endpoints
│   ├── urls.py                   # App URL routing
│   ├── serializers.py            # DRF serializers
│   ├── models.py                 # (Bo'sh - Firestore ishlatiladi)
│   ├── admin.py                  # Django admin
│   ├── apps.py                   # App config
│   └── tests.py                  # Unit tests
│
├── secrets/                       # Private files (git'ga tushmaydi)
│   └── firebase-service-account.json
│
├── venv/                          # Virtual environment
│
├── .env                           # Environment variables
├── .gitignore                     # Git ignore rules
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
│
└── Hujjatlar/
    ├── README.md                  # Tezkor kirish
    ├── SETUP_GUIDE.md             # O'rnatish qo'llanmasi
    ├── PAYME_INTEGRATION_GUIDE.md # To'liq integratsiya
    ├── TESTING_EXAMPLES.md        # Test misollar
    └── ARCHITECTURE.md            # Bu fayl
```

## 📊 Ma'lumotlar Oqimi

### 1. To'lov Havolasini Yaratish Flow

```
Client Request
    │
    ├─► POST /api/payments/create-link/
    │   Body: {"order_id": "ORD-123"}
    │
    ▼
CreatePaymentLinkView
    │
    ├─► Serializer validation
    │
    ▼
OrderService.get_order()
    │
    ├─► Firestore query
    │   db.collection('orders').document(order_id).get()
    │
    ▼
Validate order status
    │
    ├─► status != 'paid'
    ├─► status != 'cancelled'
    │
    ▼
Generate Payme checkout URL
    │
    ├─► Encode params to base64
    ├─► m: merchant_id
    ├─► ac: {order_id: "ORD-123"}
    ├─► a: amount * 100 (tiyin)
    │
    ▼
Return response
    │
    └─► {"success": true, "checkout_url": "..."}
```

### 2. Payme Webhook Flow (CheckPerformTransaction)

```
Payme Server
    │
    ├─► POST /api/payments/webhook/
    │   Headers: Authorization: Basic base64(Paycom:KEY)
    │   Body: {
    │     "jsonrpc": "2.0",
    │     "method": "CheckPerformTransaction",
    │     "params": {...}
    │   }
    │
    ▼
@payme_webhook_auth decorator
    │
    ├─► Check IP whitelist
    ├─► Parse Basic Auth header
    ├─► Verify credentials
    │
    ▼
PaymeWebhookView.post()
    │
    ├─► Parse JSON-RPC request
    ├─► Extract method name
    │
    ▼
_check_perform_transaction()
    │
    ├─► Extract order_id, amount
    │
    ▼
OrderService.get_order()
    │
    ├─► Firestore query
    │
    ▼
OrderService.validate_order_for_payment()
    │
    ├─► Check order exists
    ├─► Check status (pending/processing)
    ├─► Check amount matches
    │
    ▼
Return JSON-RPC response
    │
    └─► {"jsonrpc": "2.0", "result": {"allow": true}}
```

### 3. CreateTransaction Flow

```
Payme Server
    │
    ├─► POST /api/payments/webhook/
    │   Method: "CreateTransaction"
    │
    ▼
_create_transaction()
    │
    ├─► Check if transaction exists
    │   TransactionService.get_transaction()
    │
    ├─► If exists: return existing
    │
    ▼
Validate order
    │
    ├─► OrderService.validate_order_for_payment()
    │
    ▼
Create transaction in Firestore
    │
    ├─► TransactionService.create_transaction()
    │   db.collection('transactions').document(id).set({
    │     id: transaction_id,
    │     orderId: order_id,
    │     amount: amount,
    │     state: 1,  # CREATED
    │     createTime: timestamp,
    │     ...
    │   })
    │
    ▼
Update order status
    │
    ├─► OrderService.update_order_status()
    │   db.collection('orders').document(order_id).update({
    │     status: 'processing',
    │     paymeTransactionId: transaction_id
    │   })
    │
    ▼
Return response
    │
    └─► {
          "transaction": "...",
          "state": 1,
          "create_time": ...
        }
```

### 4. PerformTransaction Flow

```
Payme Server
    │
    ├─► POST /api/payments/webhook/
    │   Method: "PerformTransaction"
    │
    ▼
_perform_transaction()
    │
    ├─► Get transaction
    │   TransactionService.get_transaction()
    │
    ├─► Check state (must be CREATED=1)
    ├─► Check timeout (< 12 hours)
    │
    ▼
Perform transaction
    │
    ├─► TransactionService.perform_transaction()
    │   db.collection('transactions').document(id).update({
    │     state: 2,  # COMPLETED
    │     performTime: timestamp
    │   })
    │
    ▼
Update order to 'paid'
    │
    ├─► OrderService.update_order_status()
    │   db.collection('orders').document(order_id).update({
    │     status: 'paid'
    │   })
    │
    ▼
Return response
    │
    └─► {
          "transaction": "...",
          "state": 2,
          "perform_time": ...
        }
```

## 🔐 Security Layers

### 1. Authentication Layer

```python
@payme_webhook_auth decorator
    │
    ├─► IP Whitelist Check
    │   ├─► Get client IP (with proxy support)
    │   ├─► Compare with PAYME_ALLOWED_IPS
    │   └─► Reject if not in whitelist
    │
    └─► Basic Auth Check
        ├─► Parse Authorization header
        ├─► Decode base64
        ├─► Verify username = "Paycom"
        └─► Verify password = PAYME_KEY
```

**IP Whitelist (Production):**
- 185.178.51.131
- 185.178.51.132
- 195.158.31.134
- 195.158.31.10

### 2. Validation Layer

```python
OrderService.validate_order_for_payment()
    │
    ├─► Order exists check
    ├─► Status validation
    │   ├─► Not 'paid'
    │   └─► Not 'cancelled'
    │
    └─► Amount validation
        └─► expected_amount == received_amount
```

### 3. Timeout Protection

```python
TransactionService.validate_transaction_timeout()
    │
    └─► current_time - create_time <= 43200000 ms (12 hours)
```

## 📦 Data Models

### Order Document (Firestore)

```typescript
interface Order {
  orderId: string;              // "ORD-95612789"
  status: OrderStatus;          // "pending" | "processing" | "paid" | "delivered" | "cancelled"
  total: number;                // 172000 (so'mda)
  totalItems: number;           // 1
  address: string;              // "test uchun"
  phone: string;                // "+998 91 171 26 11"
  region: string;               // "Andijon"
  payment: string;              // "Payme (online to'lov)"
  delivery: string;             // "Kuryer (yetkazib berish)"
  comment?: string;             // "to'lov tizmini test qilayabman"
  items: OrderItem[];           // Mahsulotlar ro'yxati
  createdAt: number;            // Unix timestamp (ms)
  updatedAt?: number;           // Unix timestamp (ms)
  paymeTransactionId?: string;  // Payme tranzaksiya ID'si
  user?: string | null;         // User ID (agar autentifikatsiya bo'lsa)
}

interface OrderItem {
  id: string;
  title: string;
  price: number;
  quantity: number;
}
```

### Transaction Document (Firestore)

```typescript
interface Transaction {
  id: string;                   // Payme tranzaksiya ID'si
  orderId: string;              // "ORD-95612789"
  amount: number;               // 17200000 (tiyinlarda)
  state: TransactionState;      // 1 | 2 | -1 | -2
  createTime: number;           // Unix timestamp (ms)
  performTime?: number | null;  // Unix timestamp (ms)
  cancelTime?: number | null;   // Unix timestamp (ms)
  reason?: number | null;       // Cancel reason (1-5)
  account: {
    order_id: string;
  };
  createdAt: Timestamp;         // Firestore server timestamp
  updatedAt: Timestamp;         // Firestore server timestamp
}
```

### Transaction States

```python
class TransactionState:
    CREATED = 1                    # Tranzaksiya yaratilgan
    COMPLETED = 2                  # To'lov muvaffaqiyatli
    CANCELLED = -1                 # Bekor qilingan (to'lovdan oldin)
    CANCELLED_AFTER_COMPLETE = -2  # Bekor qilingan (to'lovdan keyin)
```

## 🔄 State Machine

### Order Status Transitions

```
       ┌─────────┐
       │ pending │ ◄─────────┐
       └────┬────┘            │
            │                 │
            │ CreateTransaction
            ▼                 │
     ┌─────────────┐          │
     │ processing  │          │ CancelTransaction
     └──────┬──────┘          │ (before perform)
            │                 │
            │ PerformTransaction
            ▼                 │
        ┌──────┐              │
        │ paid │──────────────┘
        └──┬───┘
           │
           │ Manual/Auto
           ▼
     ┌───────────┐
     │ delivered │
     └───────────┘
           │
           │ CancelTransaction
           │ (after perform)
           ▼
     ┌───────────┐
     │ cancelled │
     └───────────┘
```

### Transaction State Transitions

```
    ┌─────────┐
    │ CREATED │ (state = 1)
    │  (1)    │
    └────┬────┘
         │
         ├──────────┐
         │          │
         │ Perform  │ Cancel
         ▼          ▼
   ┌──────────┐  ┌───────────┐
   │COMPLETED │  │ CANCELLED │
   │   (2)    │  │    (-1)   │
   └────┬─────┘  └───────────┘
        │
        │ Cancel (refund)
        ▼
   ┌──────────────────────┐
   │CANCELLED_AFTER_COMPLETE│
   │        (-2)          │
   └──────────────────────┘
```

## ⚡ Performance Considerations

### 1. Firestore Indexes

Quyidagi query'lar uchun composite index'lar yarating:

```javascript
// Transaction by orderId
db.collection('transactions')
  .where('orderId', '==', 'ORD-123')
  .limit(1)

// Index: orderId ASC, createTime DESC
```

Firebase Console → Firestore → Indexes → Create Index

### 2. Caching Strategy

**Do NOT cache:**
- Order status (real-time data kerak)
- Transaction state (Payme bilan sinxron)

**Can cache:**
- Payme merchant ID (static)
- IP whitelist (kam o'zgaradi)

### 3. Connection Pooling

Firebase Admin SDK avtomatik connection pooling ishlatadi. Har bir request uchun yangi `firestore.client()` yaratmang - bitta global instance ishlating (`core/firebase_config.py`).

## 🔍 Monitoring va Logging

### Log Levels

```python
DEBUG   - Development debugging
INFO    - Transaction lifecycle events
WARNING - Validation failures, suspicious requests
ERROR   - System errors, Firestore failures
CRITICAL- Service unavailable
```

### Key Metrics to Monitor

1. **Transaction Metrics**
   - Transaction creation rate
   - Success rate (COMPLETED / CREATED)
   - Cancel rate
   - Average time to perform

2. **API Metrics**
   - Webhook response time
   - Authentication failures
   - Invalid requests rate

3. **Firestore Metrics**
   - Read/write operations per minute
   - Document size
   - Connection errors

## 🚨 Error Handling Strategy

### 1. Payme Errors (Client-facing)

```python
# JSON-RPC 2.0 error response
{
  "jsonrpc": "2.0",
  "id": request_id,
  "error": {
    "code": -31001,           # Payme error code
    "message": "Incorrect amount",
    "data": "Expected: 5000000, got: 4999999"
  }
}
```

### 2. Internal Errors

```python
try:
    # Business logic
except FirestoreError as e:
    logger.error(f"Firestore error: {e}")
    return PaymeError.GENERAL_ERROR
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    return PaymeError.GENERAL_ERROR
```

### 3. Idempotency

`CreateTransaction` idempotent:
```python
existing = get_transaction(transaction_id)
if existing:
    return existing  # Yangi yaratmasdan, mavjudini qaytarish
```

## 🎯 Design Decisions

### Nima uchun alohida Transactions collection?

**Pros:**
- ✅ Scalability: Orders va transactions mustaqil
- ✅ Query performance: Index'lar optimallashtirilgan
- ✅ Data integrity: To'lov tarixi saqlanadi
- ✅ Audit trail: Barcha tranzaksiyalar to'liq loglanadi
- ✅ Multiple attempts: Bir order uchun bir nechta tranzaksiya

**Cons:**
- ❌ Extra Firestore read/write operations
- ❌ Data consistency qiyinroq (transaction-level consistency yo'q)

**Alternativa:** Nested transactions in order document
- Faqat kichik scale uchun mos
- Large orders uchun document size limit muammosi

### Nima uchun Django + Firestore (SQL emas)?

**Django:**
- ✅ Batteries included (auth, admin, ORM)
- ✅ DRF - API development tez
- ✅ Firebase Admin SDK yaxshi qo'llab-quvvatlaydi

**Firestore vs PostgreSQL:**
- ✅ Real-time sync (Telegram App uchun)
- ✅ Scalability (serverless)
- ✅ Firebase ecosystem (Auth, Storage, Functions)
- ❌ Complex queries qiyin
- ❌ Transaction support cheklangan

## 📚 References

- [Payme Merchant API Docs](https://developer.help.paycom.uz/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Author:** Payme Backend Team
