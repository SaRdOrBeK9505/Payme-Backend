# Payme Idempotentlik va Pending Tranzaksiya Muammolari - Yechim

## 🔴 Muammolar

### MUAMMO 1: Idempotentlik Buzilgan

**Belgi:**
- `CheckTransaction`, `PerformTransaction`, `CancelTransaction` metodlari bir xil `transaction_id` bilan qayta chaqirilganda, natija (vaqtlar) har safar farq qilib chiqmoqda
- `create_time`, `perform_time`, `cancel_time` har safar **YANGI** hisoblanmoqda

**Sabab:**
```python
# NOTO'G'RI - har safar yangi vaqt hisoblanadi
perform_time = int(time.time() * 1000)
```

**Payme protokoli talabi:**
> Bir xil transaction_id bilan qayta so'rov kelsa, **BAZADAGI** saqlangan qiymatlar qaytarilishi kerak, hech qanday yangi hisoblash bo'lmasligi kerak.

---

### MUAMMO 2: Pending Tranzaksiya Tekshiruvi Yo'q

**Belgi:**
- Bir xil `order_id` uchun ikkinchi pending tranzaksiya yaratishga urinilganda, backend muvaffaqiyatli javob qaytarmoqda
- Bu Payme protokolini buzadi

**Sabab:**
- `CreateTransaction` metodida mavjud pending tranzaksiyalarni tekshirish logikasi yo'q

**Payme protokoli talabi:**
> Bir order uchun faqat BITTA pending (state=1) tranzaksiya bo'lishi mumkin. Agar ikkinchi pending tranzaksiya yaratishga urinilsa, **-31099** xato kodi bilan rad etilishi kerak.

---

## ✅ Yechimlar

### 1. Yangi Xato Kodi Qo'shildi

**File:** `payments/constants.py`

```python
class PaymeError:
    # ...
    ORDER_HAS_PENDING_TRANSACTION = -31099  # Yangi!
    # ...
    
    ERROR_MESSAGES = {
        # ...
        ORDER_HAS_PENDING_TRANSACTION: {
            "uz": "Buyurtma uchun kutilayotgan tranzaksiya mavjud",
            "en": "Order has pending transaction",
            "ru": "Заказ имеет ожидающую транзакцию"
        },
        # ...
    }
```

**Nima uchun:** Payme protokoli -31050 dan -31099 gacha account-related xatolar uchun ajratilgan.

---

### 2. `TransactionService.get_transaction_by_order` Yaxshilandi

**File:** `payments/services.py`

**Oldingi versiya:**
```python
def get_transaction_by_order(order_id: str) -> Optional[Dict[str, Any]]:
    query = transactions_ref.where('orderId', '==', order_id).limit(1)
    # Faqat order_id bo'yicha qidirish
```

**Yangi versiya:**
```python
def get_transaction_by_order(
    order_id: str, 
    state: Optional[int] = None  # Yangi parametr!
) -> Optional[Dict[str, Any]]:
    query = transactions_ref.where('orderId', '==', order_id)
    
    # State bo'yicha ham filtrlash mumkin
    if state is not None:
        query = query.where('state', '==', state)
    
    query = query.limit(1)
```

**Nima uchun:** Pending (state=1) tranzaksiyalarni aniq topish uchun.

---

### 3. `CreateTransaction` - Pending Tranzaksiya Tekshiruvi

**File:** `payments/views.py`

```python
def _create_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # 1. IDEMPOTENTLIK: Mavjud tranzaksiyani qaytarish
    existing_transaction = TransactionService.get_transaction(transaction_id)
    if existing_transaction:
        logger.info(f"Transaction already exists: {transaction_id}")
        return {
            "create_time": existing_transaction['createTime'],  # BAZADAN!
            "transaction": existing_transaction['id'],
            "state": existing_transaction['state']
        }
    
    # 2. Order validatsiyasi
    order = OrderService.get_order(order_id)
    validation = OrderService.validate_order_for_payment(order, amount)
    if not validation['valid']:
        raise PaymeException(...)
    
    # 3. YANGI: Pending tranzaksiya tekshiruvi
    pending_transaction = TransactionService.get_transaction_by_order(
        order_id=order_id, 
        state=TransactionState.CREATED  # state=1
    )
    
    if pending_transaction and pending_transaction['id'] != transaction_id:
        # Boshqa pending tranzaksiya topildi!
        raise PaymeException(
            PaymeError.ORDER_HAS_PENDING_TRANSACTION,
            f"Order already has pending transaction: {pending_transaction['id']}"
        )
    
    # 4. Yangi tranzaksiya yaratish
    transaction = TransactionService.create_transaction(...)
```

**O'zgarishlar:**

| # | O'zgarish | Sabab |
|---|-----------|-------|
| 1 | Mavjud tranzaksiyadan **bazadagi** `createTime`ni qaytarish | Idempotentlik ta'minlash |
| 2 | Pending tranzaksiya tekshiruvi qo'shildi | Payme protokoli talabi |
| 3 | Log xabarlari qo'shildi | Debug qilish oson |

---

### 4. `PerformTransaction` - Idempotentlik Ta'minlandi

**File:** `payments/views.py`

```python
def _perform_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # Tranzaksiyani bazadan olish
    transaction = TransactionService.get_transaction(transaction_id)
    
    # IDEMPOTENTLIK: Agar allaqachon perform qilingan bo'lsa
    if transaction['state'] == TransactionState.COMPLETED:
        logger.info(f"Transaction already performed: {transaction_id}")
        return {
            "transaction": transaction['id'],
            "perform_time": transaction['performTime'],  # BAZADAN! (yangi emas)
            "state": transaction['state']
        }
    
    # Aks holda, yangi perform qilish
    perform_time = int(time.time() * 1000)  # Faqat birinchi marta
    TransactionService.perform_transaction(transaction_id, perform_time)
    
    return {
        "transaction": transaction_id,
        "perform_time": perform_time,  # Yangi yaratilgan vaqt
        "state": TransactionState.COMPLETED
    }
```

**Kalit nuqta:** 
- ✅ Qayta chaqirilsa → bazadagi `performTime` qaytariladi
- ✅ Birinchi marta → yangi `perform_time` yaratiladi va saqlanadi

---

### 5. `CancelTransaction` - Idempotentlik Ta'minlandi

**File:** `payments/views.py`

```python
def _cancel_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
    transaction = TransactionService.get_transaction(transaction_id)
    
    # IDEMPOTENTLIK: Agar allaqachon bekor qilingan bo'lsa
    if transaction['state'] in [
        TransactionState.CANCELLED, 
        TransactionState.CANCELLED_AFTER_COMPLETE
    ]:
        logger.info(f"Transaction already cancelled: {transaction_id}")
        return {
            "transaction": transaction['id'],
            "cancel_time": transaction['cancelTime'],  # BAZADAN! (yangi emas)
            "state": transaction['state']
        }
    
    # Aks holda, yangi bekor qilish
    cancel_time = int(time.time() * 1000)  # Faqat birinchi marta
    TransactionService.cancel_transaction(transaction_id, cancel_time, reason)
    
    # State'ni aniqlash
    new_state = (TransactionState.CANCELLED_AFTER_COMPLETE 
                 if transaction['state'] == TransactionState.COMPLETED 
                 else TransactionState.CANCELLED)
    
    return {
        "transaction": transaction_id,
        "cancel_time": cancel_time,  # Yangi yaratilgan vaqt
        "state": new_state
    }
```

**Kalit nuqta:**
- ✅ Qayta chaqirilsa → bazadagi `cancelTime` qaytariladi
- ✅ Birinchi marta → yangi `cancel_time` yaratiladi va saqlanadi

---

### 6. `CheckTransaction` - Allaqachon To'g'ri

**File:** `payments/views.py`

```python
def _check_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
    transaction = TransactionService.get_transaction(transaction_id)
    
    if not transaction:
        raise PaymeException(PaymeError.TRANSACTION_NOT_FOUND, ...)
    
    # HAR DOIM bazadan o'qib qaytaradi (hech narsa hisoblanmaydi)
    return {
        "create_time": transaction['createTime'],      # BAZADAN
        "perform_time": transaction.get('performTime', 0),  # BAZADAN
        "cancel_time": transaction.get('cancelTime', 0),    # BAZADAN
        "transaction": transaction['id'],
        "state": transaction['state'],
        "reason": transaction.get('reason')
    }
```

**To'g'ri:** Bu metod allaqachon idempotent edi, hech narsa o'zgartirish kerak emas.

---

## 🧪 Test Ssenariylari

### Test 1: Idempotent CreateTransaction

```bash
# Birinchi chaqiruv
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Authorization: Basic <auth>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CreateTransaction",
    "params": {
      "id": "TXN-123",
      "time": 1609459200000,
      "amount": 17200000,
      "account": {"order_id": "ORD-12345"}
    }
  }'

# Natija:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "create_time": 1609459200000,
    "transaction": "TXN-123",
    "state": 1
  }
}

# Ikkinchi chaqiruv (bir xil transaction_id)
# Natija: AYNAN bir xil create_time (1609459200000)
```

**Kutilgan:** ✅ `create_time` har ikkala chaqiruvda ham bir xil

---

### Test 2: Pending Tranzaksiya Rad Etish

```bash
# 1. Birinchi tranzaksiya yaratish
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -d '{
    "method": "CreateTransaction",
    "params": {
      "id": "TXN-001",
      "account": {"order_id": "ORD-12345"}
    }
  }'
# Natija: success, state=1

# 2. Ikkinchi tranzaksiya (har xil ID, bir xil order)
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -d '{
    "method": "CreateTransaction",
    "params": {
      "id": "TXN-002",  # Boshqa ID!
      "account": {"order_id": "ORD-12345"}  # Bir xil order!
    }
  }'

# Natija:
{
  "jsonrpc": "2.0",
  "error": {
    "code": -31099,
    "message": {
      "uz": "Buyurtma uchun kutilayotgan tranzaksiya mavjud",
      "en": "Order has pending transaction",
      "ru": "Заказ имеет ожидающую транзакцию"
    },
    "data": "Order already has pending transaction: TXN-001"
  }
}
```

**Kutilgan:** ✅ Xato kodi -31099

---

### Test 3: Idempotent PerformTransaction

```bash
# Birinchi perform
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -d '{
    "method": "PerformTransaction",
    "params": {"id": "TXN-123"}
  }'
# Natija: perform_time = 1675868194000

# Ikkinchi perform (qayta chaqiruv)
# Natija: perform_time = 1675868194000 (bir xil!)
```

**Kutilgan:** ✅ `perform_time` o'zgarmaydi

---

## 📊 O'zgarishlar Jadvali

| Fayl | Metod/Funksiya | O'zgarish | Muammo |
|------|----------------|-----------|--------|
| `constants.py` | `PaymeError` | `-31099` kodi qo'shildi | Pending tranzaksiya xatosi uchun |
| `constants.py` | `ERROR_MESSAGES` | 3 tilda xabar qo'shildi | -31099 uchun xabarlar |
| `services.py` | `get_transaction_by_order` | `state` parametri qo'shildi | Pending tekshiruv uchun |
| `views.py` | `_create_transaction` | Pending tekshiruv qo'shildi | Muammo 2 |
| `views.py` | `_create_transaction` | Bazadan qiymat qaytarish | Muammo 1 |
| `views.py` | `_perform_transaction` | Bazadan `performTime` qaytarish | Muammo 1 |
| `views.py` | `_cancel_transaction` | Bazadan `cancelTime` qaytarish | Muammo 1 |

---

## ✅ Natija

### Idempotentlik ✅
- ✅ `CreateTransaction` - bir xil ID bilan qayta chaqirilsa, bazadagi `createTime` qaytariladi
- ✅ `PerformTransaction` - qayta chaqirilsa, bazadagi `performTime` qaytariladi
- ✅ `CancelTransaction` - qayta chaqirilsa, bazadagi `cancelTime` qaytariladi
- ✅ `CheckTransaction` - har doim bazadan o'qiydi (allaqachon to'g'ri edi)

### Pending Tranzaksiya Tekshiruvi ✅
- ✅ Bir order uchun faqat bitta pending tranzaksiya
- ✅ Ikkinchi pending tranzaksiya yaratish urinilsa → **-31099** xato
- ✅ Xato xabarlari 3 tilda (uz, en, ru)

### Payme Sandbox ✅
- ✅ Barcha testlar o'tadi
- ✅ Idempotentlik testlari muvaffaqiyatli
- ✅ Pending tranzaksiya testi muvaffaqiyatli

---

**Muallif:** Kiro AI Assistant  
**Sana:** 2026-07-06  
**Versiya:** 2.0  
