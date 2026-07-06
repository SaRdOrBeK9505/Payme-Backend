"""
Payme Merchant API konstantalari va konfiguratsiyalar.
Bu faylda Payme bilan ishlash uchun kerakli barcha konstantalar joylashgan.
"""

# Payme JSON-RPC metod nomlari
class PaymeMethod:
    """Payme Merchant API metodlari"""
    CHECK_PERFORM_TRANSACTION = "CheckPerformTransaction"
    CREATE_TRANSACTION = "CreateTransaction"
    PERFORM_TRANSACTION = "PerformTransaction"
    CANCEL_TRANSACTION = "CancelTransaction"
    CHECK_TRANSACTION = "CheckTransaction"


# Payme xato kodlari (JSON-RPC 2.0 standartiga muvofiq)
class PaymeError:
    """Payme xato kodlari va ularga mos xabarlar"""
    
    # JSON-RPC standart xatolari
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Payme biznes xatolari
    TRANSPORT_ERROR = -32300
    ACCESS_DENIED = -32504
    USER_NOT_FOUND = -31050
    INCORRECT_AMOUNT = -31001
    ORDER_NOT_FOUND = -31050
    ORDER_ALREADY_PAID = -31051
    ORDER_CANCELLED = -31008
    ORDER_HAS_PENDING_TRANSACTION = -31099  # Order uchun pending tranzaksiya mavjud
    TRANSACTION_NOT_FOUND = -31003
    TRANSACTION_ALREADY_CANCELLED = -31007
    TRANSACTION_CANNOT_BE_CANCELLED = -31008
    GENERAL_ERROR = -32000
    
    # Xato xabarlari (o'zbek va ingliz tillarida)
    ERROR_MESSAGES = {
        PARSE_ERROR: {
            "uz": "JSON parse xatosi",
            "en": "Parse error",
            "ru": "Ошибка парсинга JSON"
        },
        INVALID_REQUEST: {
            "uz": "Noto'g'ri so'rov",
            "en": "Invalid request",
            "ru": "Неверный запрос"
        },
        METHOD_NOT_FOUND: {
            "uz": "Metod topilmadi",
            "en": "Method not found",
            "ru": "Метод не найден"
        },
        INVALID_PARAMS: {
            "uz": "Noto'g'ri parametrlar",
            "en": "Invalid params",
            "ru": "Неверные параметры"
        },
        INTERNAL_ERROR: {
            "uz": "Ichki server xatosi",
            "en": "Internal error",
            "ru": "Внутренняя ошибка"
        },
        ACCESS_DENIED: {
            "uz": "Metodni bajarish uchun huquq yetarli emas",
            "en": "Insufficient privilege to execute method",
            "ru": "Недостаточно привилегий для выполнения метода"
        },
        INCORRECT_AMOUNT: {
            "uz": "Noto'g'ri summa",
            "en": "Incorrect amount",
            "ru": "Неверная сумма"
        },
        ORDER_NOT_FOUND: {
            "uz": "Buyurtma topilmadi",
            "en": "Order not found",
            "ru": "Заказ не найден"
        },
        ORDER_ALREADY_PAID: {
            "uz": "Buyurtma allaqachon to'langan",
            "en": "Order already paid",
            "ru": "Заказ уже оплачен"
        },
        ORDER_CANCELLED: {
            "uz": "Buyurtma bekor qilingan",
            "en": "Order cancelled",
            "ru": "Заказ отменен"
        },
        ORDER_HAS_PENDING_TRANSACTION: {
            "uz": "Buyurtma uchun kutilayotgan tranzaksiya mavjud",
            "en": "Order has pending transaction",
            "ru": "Заказ имеет ожидающую транзакцию"
        },
        TRANSACTION_NOT_FOUND: {
            "uz": "Tranzaksiya topilmadi",
            "en": "Transaction not found",
            "ru": "Транзакция не найдена"
        },
        TRANSACTION_ALREADY_CANCELLED: {
            "uz": "Tranzaksiya allaqachon bekor qilingan",
            "en": "Transaction already cancelled",
            "ru": "Транзакция уже отменена"
        },
        TRANSACTION_CANNOT_BE_CANCELLED: {
            "uz": "Tranzaksiyani bekor qilib bo'lmaydi",
            "en": "Transaction cannot be cancelled",
            "ru": "Транзакцию нельзя отменить"
        },
        GENERAL_ERROR: {
            "uz": "Umumiy server xatosi",
            "en": "General server error",
            "ru": "Общая ошибка сервера"
        },
    }
    
    @classmethod
    def get_error_message(cls, code: int, lang: str = "uz") -> str:
        """
        Xato kodi bo'yicha xabarni qaytaradi.
        
        Args:
            code: Xato kodi
            lang: Til kodi (uz, en, ru)
            
        Returns:
            Xato xabari
        """
        return cls.ERROR_MESSAGES.get(code, {}).get(lang, "Unknown error")


# Tranzaksiya holatlari
class TransactionState:
    """Payme tranzaksiya holatlari"""
    CREATED = 1  # Tranzaksiya yaratilgan, lekin hali to'lov amalga oshirilmagan
    COMPLETED = 2  # Tranzaksiya muvaffaqiyatli yakunlangan (to'lov qabul qilingan)
    CANCELLED = -1  # Tranzaksiya bekor qilingan (client yoki timeout tufayli)
    CANCELLED_AFTER_COMPLETE = -2  # Tranzaksiya to'lovdan keyin bekor qilingan


# Order holatlari
class OrderStatus:
    """Order holatlari (Firestore collection'da saqlanadi)"""
    PENDING = "pending"  # Yangi order, to'lov kutilmoqda
    PROCESSING = "processing"  # To'lov jarayonida (tranzaksiya yaratilgan)
    PAID = "paid"  # To'lov muvaffaqiyatli amalga oshirilgan
    DELIVERED = "delivered"  # Yetkazib berilgan
    CANCELLED = "cancelled"  # Bekor qilingan


# Payme timeout konstantalari (millisekundlarda)
class PaymeTimeout:
    """Payme timeout qiymatlari"""
    CHECK_PERFORM = 43200000  # 12 soat - CheckPerformTransaction uchun
    CREATE_TRANSACTION = 43200000  # 12 soat - CreateTransaction uchun
    CANCEL_TIMEOUT = 43200000  # 12 soat - bekor qilish uchun


# Payme URL'lari
class PaymeURL:
    """Payme checkout URL'lari"""
    PRODUCTION = "https://checkout.paycom.uz"
    TEST = "https://checkout.test.paycom.uz"


# Firestore collection nomlari
class FirestoreCollection:
    """Firestore collection nomlari"""
    ORDERS = "orders"
    TRANSACTIONS = "transactions"


# Payme account field nomi (settings.py'dan olinadi)
PAYME_ACCOUNT_KEY = "order_id"  # Payme'ga yuborilganda key sifatida ishlatiladi
