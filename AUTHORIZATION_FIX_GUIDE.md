# Payme Authorization Muammosi - Yechim

## 🔴 Muammo

Payme Sandbox test.paycom.uz orqali test qilganda, **barcha metodlarda** "noto'g'ri Authorization" testi muvaffaqiyatsiz chiqdi:

- ❌ HTTP 403 Forbidden
- ❌ Response: `{"detail": "Invalid username/password."}`

**Kutilgan natija:**
- ✅ HTTP 200 OK
- ✅ Response: JSON-RPC formatida -32504 xato kodi

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32504,
    "message": {
      "uz": "Metodni bajarish uchun huquq yetarli emas",
      "en": "Insufficient privilege to execute method",
      "ru": "Недостаточно привилегий для выполнения метода"
    }
  },
  "id": null
}
```

## 🔍 Muammoning Sababi

**DRF'ning `APIView` klassi avtomatik ravishda authentication/permission check'larini bajaradi.**

Qachon Authorization header mavjud lekin noto'g'ri bo'lsa, DRF:
1. So'rovni view'ga yetkazmasdan
2. O'zining standart exception handler'i orqali
3. HTTP 403 status kodi bilan javob qaytaradi

```
HTTP Request → DRF APIView → Auto Auth Check → ❌ 403 (view'ga yetmadi!)
                                              ↓
                                    {"detail": "Invalid username/password."}
```

**Siz yozgan `@payme_webhook_auth` decorator view ichida ishlaydi, lekin DRF'ning auto-auth unga yetishdan oldin to'xtatib qo'yadi!**

## ✅ Yechim

### 1. `views.py` - DRF Auto-Auth'ni O'chirish

`PaymeWebhookView` klassiga quyidagilarni qo'shdik:

```python
class PaymeWebhookView(APIView):
    """Payme Merchant API webhook endpointi."""
    
    # MUHIM: DRF'ning auto-authentication'ini o'chirish
    # Barcha authentication decorator orqali qo'lda boshqariladi
    authentication_classes = []
    permission_classes = []
    
    @payme_webhook_auth
    def post(self, request: Request) -> JsonResponse:
        # ...
```

Bu DRF'ga aytadi: "Sen hech qanday auth check qilma, men o'zim boshqaraman!"

### 2. `authentication.py` - To'g'ri Format Xato Javoblar

Decorator'dagi barcha xato javoblarni Payme protokoliga moslashtirildi:

**Oldingi format (noto'g'ri):**
```python
"message": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en")
```

**Yangi format (to'g'ri - 3 tilda):**
```python
"message": {
    "uz": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "uz"),
    "en": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en"),
    "ru": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "ru")
}
```

### 3. `constants.py` - ACCESS_DENIED Xabarini Qo'shish

`PaymeError.ERROR_MESSAGES` dictionary'ga -32504 uchun xabarlar qo'shildi:

```python
ACCESS_DENIED: {
    "uz": "Metodni bajarish uchun huquq yetarli emas",
    "en": "Insufficient privilege to execute method",
    "ru": "Недостаточно привилегий для выполнения метода"
}
```

### 4. `views.py` - `_error_response` Metodini Yangilash

Barcha view metodlari uchun ham 3 tilda xato javob qaytarish:

```python
@staticmethod
def _error_response(request_id: Any, code: int, message: str, 
                   data: Any = None) -> JsonResponse:
    error_body = {
        "code": code,
        "message": {
            "uz": PaymeError.get_error_message(code, "uz"),
            "en": PaymeError.get_error_message(code, "en"),
            "ru": PaymeError.get_error_message(code, "ru")
        },
        "data": data if data is not None else message
    }
    return JsonResponse({
        "jsonrpc": "2.0",
        "error": error_body,
        "id": request_id
    }, status=200)  # MUHIM: Har doim HTTP 200!
```

## 🧪 Test Qilish

### 1. Server'ni Ishga Tushirish

```bash
python manage.py runserver
```

### 2. Noto'g'ri Authorization bilan Test

```bash
curl -X POST https://payme-api.medhomee.uz/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic base64(Paycom:NOTO'G'RI_PAROL)" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 17200000,
      "account": {"order_id": "ORD-12345"}
    }
  }'
```

**Kutilayotgan javob:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32504,
    "message": {
      "uz": "Metodni bajarish uchun huquq yetarli emas",
      "en": "Insufficient privilege to execute method",
      "ru": "Недостаточно привилегий для выполнения метода"
    },
    "data": "Invalid username or password"
  },
  "id": null
}
```

**Status Code:** `200 OK` ✅

### 3. Authorization Header Bo'lmagan Test

```bash
curl -X POST https://payme-api.medhomee.uz/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 17200000,
      "account": {"order_id": "ORD-12345"}
    }
  }'
```

**Kutilayotgan javob:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32504,
    "message": {
      "uz": "Metodni bajarish uchun huquq yetarli emas",
      "en": "Insufficient privilege to execute method",
      "ru": "Недостаточно привилегий для выполнения метода"
    },
    "data": "Authorization header is missing"
  },
  "id": null
}
```

**Status Code:** `200 OK` ✅

### 4. To'g'ri Authorization bilan Test

```bash
# Avval to'g'ri Basic Auth string yaratish
echo -n "Paycom:YOUR_PAYME_KEY" | base64

# Keyin test qilish
curl -X POST https://payme-api.medhomee.uz/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <yuqoridagi_base64_string>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
      "amount": 17200000,
      "account": {"order_id": "ORD-12345"}
    }
  }'
```

**Kutilayotgan javob:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "allow": true
  }
}
```

**Status Code:** `200 OK` ✅

## 📊 O'zgarishlar Jadvali

| Fayl | O'zgarish | Sabab |
|------|-----------|-------|
| `views.py` | `authentication_classes = []`<br>`permission_classes = []` | DRF auto-auth'ni o'chirish |
| `views.py` | `_error_response` - 3 tilda xabar | Payme protokoli talabi |
| `authentication.py` | Barcha xato javoblarda 3 tilda xabar | Payme protokoli talabi |
| `constants.py` | `ACCESS_DENIED` xabarlarini qo'shish | -32504 uchun to'liq xabar |

## 🎯 Natija

✅ Authorization header mavjud lekin noto'g'ri → HTTP 200 + JSON-RPC -32504  
✅ Authorization header yo'q → HTTP 200 + JSON-RPC -32504  
✅ Authorization to'g'ri → HTTP 200 + method natijasi  
✅ Barcha xato javoblar 3 tilda (uz, en, ru)  
✅ DRF'ning 403 xatosi hech qachon qaytarilmaydi  

## 🔐 Xavfsizlik

Bu yechim xavfsizlikni **kamaytirmaydi**, balki **to'g'ri formatda** qaytaradi:

- ❌ Noto'g'ri login/parol → ruxsat berilmaydi
- ❌ IP whitelist'da yo'q → ruxsat berilmaydi
- ✅ Faqat javob formati o'zgaradi (DRF 403 → JSON-RPC -32504)

---

**Muallif:** Kiro AI Assistant  
**Sana:** 2026-07-06  
**Versiya:** 1.0  
