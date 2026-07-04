"""
Payme Integration Unit Tests

Bu faylda payments app uchun unit testlar joylashgan.
Ishlatish: python manage.py test payments
"""

from django.test import TestCase, override_settings
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
import base64
import json
import time

from .constants import (
    PaymeError,
    PaymeMethod,
    TransactionState,
    OrderStatus
)
from .services import OrderService, TransactionService
from .authentication import (
    parse_basic_auth,
    verify_payme_credentials,
    get_client_ip
)


class BasicAuthTestCase(TestCase):
    """Basic Authentication test'lari"""
    
    def test_parse_basic_auth_valid(self):
        """Valid Basic Auth header'ni parse qilish"""
        username = "Paycom"
        password = "test_key"
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        auth_header = f"Basic {encoded}"
        
        result = parse_basic_auth(auth_header)
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], username)
        self.assertEqual(result[1], password)
    
    def test_parse_basic_auth_invalid_format(self):
        """Noto'g'ri format"""
        result = parse_basic_auth("Bearer token123")
        self.assertIsNone(result)
    
    def test_parse_basic_auth_no_prefix(self):
        """Basic prefix'siz"""
        result = parse_basic_auth("dGVzdDp0ZXN0")
        self.assertIsNone(result)
    
    @override_settings(PAYME_KEY='test_key_123')
    def test_verify_payme_credentials_valid(self):
        """To'g'ri credentials"""
        result = verify_payme_credentials("Paycom", "test_key_123")
        self.assertTrue(result)
    
    @override_settings(PAYME_KEY='test_key_123')
    def test_verify_payme_credentials_invalid(self):
        """Noto'g'ri credentials"""
        result = verify_payme_credentials("Paycom", "wrong_key")
        self.assertFalse(result)
        
        result = verify_payme_credentials("WrongUser", "test_key_123")
        self.assertFalse(result)


class ClientIPTestCase(TestCase):
    """Client IP detection test'lari"""
    
    def test_get_client_ip_direct(self):
        """Direct connection"""
        request = Mock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_forwarded(self):
        """X-Forwarded-For orqali"""
        request = Mock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.1.1',
            'REMOTE_ADDR': '192.168.1.1'
        }
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')


class OrderServiceTestCase(TestCase):
    """OrderService test'lari"""
    
    @patch('payments.services.db')
    def test_get_order_exists(self, mock_db):
        """Mavjud order'ni olish"""
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.id = "ORD-123"
        mock_doc.to_dict.return_value = {
            'orderId': 'ORD-123',
            'status': 'pending',
            'total': 50000
        }
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        # Test
        order = OrderService.get_order("ORD-123")
        
        self.assertIsNotNone(order)
        self.assertEqual(order['orderId'], 'ORD-123')
        self.assertEqual(order['id'], 'ORD-123')
    
    @patch('payments.services.db')
    def test_get_order_not_exists(self, mock_db):
        """Mavjud emas order"""
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        order = OrderService.get_order("ORD-NONEXIST")
        self.assertIsNone(order)
    
    def test_validate_order_not_found(self):
        """Order topilmasa"""
        validation = OrderService.validate_order_for_payment(None, 5000000)
        
        self.assertFalse(validation['valid'])
        self.assertEqual(validation['error_code'], PaymeError.ORDER_NOT_FOUND)
    
    def test_validate_order_already_paid(self):
        """Order allaqachon to'langan"""
        order = {
            'orderId': 'ORD-123',
            'status': OrderStatus.PAID,
            'total': 50000
        }
        
        validation = OrderService.validate_order_for_payment(order, 5000000)
        
        self.assertFalse(validation['valid'])
        self.assertEqual(validation['error_code'], PaymeError.ORDER_ALREADY_PAID)
    
    def test_validate_order_incorrect_amount(self):
        """Noto'g'ri summa"""
        order = {
            'orderId': 'ORD-123',
            'status': OrderStatus.PENDING,
            'total': 50000
        }
        
        # Expected: 5000000 tiyin (50000 so'm * 100)
        # Received: 4999999 tiyin
        validation = OrderService.validate_order_for_payment(order, 4999999)
        
        self.assertFalse(validation['valid'])
        self.assertEqual(validation['error_code'], PaymeError.INCORRECT_AMOUNT)
    
    def test_validate_order_success(self):
        """Muvaffaqiyatli validatsiya"""
        order = {
            'orderId': 'ORD-123',
            'status': OrderStatus.PENDING,
            'total': 50000
        }
        
        validation = OrderService.validate_order_for_payment(order, 5000000)
        
        self.assertTrue(validation['valid'])


class TransactionServiceTestCase(TestCase):
    """TransactionService test'lari"""
    
    def test_validate_transaction_timeout_within_limit(self):
        """Timeout muddat ichida"""
        create_time = int(time.time() * 1000) - 1000000  # 1000 soniya oldin
        current_time = int(time.time() * 1000)
        
        result = TransactionService.validate_transaction_timeout(create_time, current_time)
        self.assertTrue(result)
    
    def test_validate_transaction_timeout_exceeded(self):
        """Timeout muddat o'tgan"""
        create_time = int(time.time() * 1000) - 50000000  # 50000 soniya oldin (12 soatdan ko'p)
        current_time = int(time.time() * 1000)
        
        result = TransactionService.validate_transaction_timeout(create_time, current_time)
        self.assertFalse(result)
    
    @patch('payments.services.db')
    def test_create_transaction(self, mock_db):
        """Tranzaksiya yaratish"""
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        transaction_id = "test_trans_001"
        order_id = "ORD-123"
        amount = 5000000
        create_time = int(time.time() * 1000)
        account = {"order_id": order_id}
        
        transaction = TransactionService.create_transaction(
            transaction_id=transaction_id,
            order_id=order_id,
            amount=amount,
            create_time=create_time,
            account=account
        )
        
        self.assertEqual(transaction['id'], transaction_id)
        self.assertEqual(transaction['orderId'], order_id)
        self.assertEqual(transaction['amount'], amount)
        self.assertEqual(transaction['state'], TransactionState.CREATED)


class PaymeConstantsTestCase(TestCase):
    """Payme konstantalar test'lari"""
    
    def test_error_messages_exist(self):
        """Xato xabarlari mavjudligi"""
        from .constants import PaymeError
        
        # Asosiy xato kodlari uchun xabarlar mavjud bo'lishi kerak
        error_codes = [
            PaymeError.PARSE_ERROR,
            PaymeError.INVALID_REQUEST,
            PaymeError.METHOD_NOT_FOUND,
            PaymeError.INVALID_PARAMS,
            PaymeError.INCORRECT_AMOUNT,
            PaymeError.ORDER_NOT_FOUND,
        ]
        
        for code in error_codes:
            message = PaymeError.get_error_message(code, "en")
            self.assertIsNotNone(message)
            self.assertNotEqual(message, "Unknown error")
    
    def test_transaction_states(self):
        """Transaction state'lar"""
        self.assertEqual(TransactionState.CREATED, 1)
        self.assertEqual(TransactionState.COMPLETED, 2)
        self.assertEqual(TransactionState.CANCELLED, -1)
        self.assertEqual(TransactionState.CANCELLED_AFTER_COMPLETE, -2)


class PaymeWebhookIntegrationTestCase(TestCase):
    """Payme webhook integration test'lari"""
    
    def setUp(self):
        """Test setup"""
        self.client_class = self.client.__class__
        self.payme_key = settings.PAYME_KEY or "test_key"
        
        # Basic Auth header yaratish
        credentials = f"Paycom:{self.payme_key}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        self.auth_header = f"Basic {encoded}"
    
    def test_webhook_without_auth(self):
        """Auth header'siz so'rov"""
        response = self.client.post(
            '/api/payments/webhook/',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "CheckTransaction",
                "params": {"id": "test"}
            }),
            content_type='application/json'
        )
        
        # 401 Unauthorized kutiladi
        self.assertIn(response.status_code, [401, 403])
    
    def test_webhook_invalid_json(self):
        """Noto'g'ri JSON format"""
        with override_settings(PAYME_KEY=self.payme_key, PAYME_ALLOWED_IPS=['']):
            response = self.client.post(
                '/api/payments/webhook/',
                data="invalid json",
                content_type='application/json',
                HTTP_AUTHORIZATION=self.auth_header
            )
            
            # Parse error kutiladi
            data = response.json()
            self.assertEqual(data.get('error', {}).get('code'), PaymeError.PARSE_ERROR)
    
    def test_webhook_method_not_found(self):
        """Mavjud bo'lmagan metod"""
        with override_settings(PAYME_KEY=self.payme_key, PAYME_ALLOWED_IPS=['']):
            response = self.client.post(
                '/api/payments/webhook/',
                data=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "NonExistentMethod",
                    "params": {}
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=self.auth_header
            )
            
            data = response.json()
            self.assertEqual(data.get('error', {}).get('code'), PaymeError.METHOD_NOT_FOUND)


# Integration test uchun helper
def create_test_order_in_firestore():
    """Test order yaratish (integration test uchun)"""
    from core.firebase_config import db
    
    order_data = {
        'orderId': 'ORD-TEST-UNIT',
        'status': 'pending',
        'total': 50000,
        'totalItems': 1,
        'address': 'Test address',
        'phone': '+998901234567',
        'region': 'Test',
        'payment': 'Payme',
        'delivery': 'Test',
        'items': [],
        'createdAt': int(time.time() * 1000)
    }
    
    db.collection('orders').document('ORD-TEST-UNIT').set(order_data)
    return 'ORD-TEST-UNIT'


def cleanup_test_order_in_firestore(order_id):
    """Test order'ni o'chirish"""
    from core.firebase_config import db
    db.collection('orders').document(order_id).delete()


# Test running instructions
"""
Testlarni ishga tushirish:

1. Barcha testlar:
   python manage.py test payments

2. Bitta test class:
   python manage.py test payments.tests.BasicAuthTestCase

3. Bitta test method:
   python manage.py test payments.tests.BasicAuthTestCase.test_parse_basic_auth_valid

4. Verbose mode:
   python manage.py test payments --verbosity=2

5. Coverage bilan:
   pip install coverage
   coverage run --source='payments' manage.py test payments
   coverage report
   coverage html  # HTML report
"""
