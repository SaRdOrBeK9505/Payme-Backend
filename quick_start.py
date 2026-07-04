#!/usr/bin/env python
"""
Payme Backend - Quick Start Test Script

Bu script asosiy funksionallikni tezkor test qilish uchun.
Ishlatish: python quick_start.py
"""

import os
import sys
import django

# Django settings'ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import json
import base64
from payments.services import OrderService, TransactionService
from payments.constants import OrderStatus, TransactionState


def print_header(text):
    """Chiroyli header chop etish"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    """Success xabar"""
    print(f"✅ {text}")


def print_error(text):
    """Error xabar"""
    print(f"❌ {text}")


def print_info(text):
    """Info xabar"""
    print(f"ℹ️  {text}")


def check_environment():
    """Environment variables tekshirish"""
    print_header("1. Environment Variables Tekshiruvi")
    
    from django.conf import settings
    
    checks = {
        "PAYME_MERCHANT_ID": settings.PAYME_MERCHANT_ID,
        "PAYME_KEY": settings.PAYME_KEY,
        "PAYME_ACCOUNT_FIELD": settings.PAYME_ACCOUNT_FIELD,
    }
    
    all_ok = True
    for key, value in checks.items():
        if value:
            print_success(f"{key}: {'*' * 10} (configured)")
        else:
            print_error(f"{key}: NOT SET!")
            all_ok = False
    
    return all_ok


def check_firebase():
    """Firebase connection tekshirish"""
    print_header("2. Firebase Connection Tekshiruvi")
    
    try:
        from core.firebase_config import db
        
        # Test collection'ga yozish va o'qish
        test_ref = db.collection('_test_connection')
        test_doc = test_ref.document('test')
        
        test_doc.set({'test': True, 'timestamp': 'test'})
        doc = test_doc.get()
        
        if doc.exists:
            print_success("Firebase Firestore connection - OK")
            test_doc.delete()  # Test doc'ni o'chirish
            return True
        else:
            print_error("Firebase Firestore connection - FAILED")
            return False
            
    except Exception as e:
        print_error(f"Firebase error: {str(e)}")
        return False


def check_orders_collection():
    """Orders collection tekshirish"""
    print_header("3. Orders Collection Tekshiruvi")
    
    try:
        from core.firebase_config import db
        
        # Orders collection'dagi birinchi 5 ta doc'ni olish
        orders_ref = db.collection('orders').limit(5)
        orders = orders_ref.get()
        
        order_count = len(orders)
        print_info(f"Orders collection'da {order_count} ta order topildi")
        
        if order_count > 0:
            print_success("Orders collection - OK")
            print("\nNamuna order'lar:")
            for idx, order in enumerate(orders, 1):
                order_data = order.to_dict()
                print(f"  {idx}. Order ID: {order.id}")
                print(f"     Status: {order_data.get('status', 'N/A')}")
                print(f"     Total: {order_data.get('total', 0)} so'm")
                print()
            return True
        else:
            print_error("Orders collection bo'sh!")
            print_info("Test order yaratish uchun Firestore Console'dan foydalaning")
            print_info("Yoki SETUP_GUIDE.md faylini o'qing")
            return False
            
    except Exception as e:
        print_error(f"Orders collection error: {str(e)}")
        return False


def test_order_service():
    """OrderService test qilish"""
    print_header("4. OrderService Test")
    
    try:
        # Birinchi order'ni olish
        from core.firebase_config import db
        orders_ref = db.collection('orders').limit(1)
        orders = orders_ref.get()
        
        if not orders:
            print_error("Test qilish uchun order yo'q")
            return False
        
        order_id = orders[0].id
        print_info(f"Test order ID: {order_id}")
        
        # OrderService.get_order() test
        order = OrderService.get_order(order_id)
        if order:
            print_success(f"OrderService.get_order() - OK")
            print(f"   Status: {order.get('status')}")
            print(f"   Total: {order.get('total')} so'm")
        else:
            print_error("OrderService.get_order() - FAILED")
            return False
        
        # OrderService.validate_order_for_payment() test
        amount = order.get('total', 0) * 100  # so'mdan tiyinga
        validation = OrderService.validate_order_for_payment(order, amount)
        
        if validation['valid']:
            print_success("OrderService.validate_order_for_payment() - OK")
        else:
            print_info(f"Validation: {validation['error_message']}")
        
        return True
        
    except Exception as e:
        print_error(f"OrderService error: {str(e)}")
        return False


def test_payment_link_generation():
    """To'lov havolasi yaratish test"""
    print_header("5. To'lov Havolasi Yaratish Test")
    
    try:
        from django.conf import settings
        from payments.views import CreatePaymentLinkView
        
        # Birinchi order'ni olish
        from core.firebase_config import db
        orders_ref = db.collection('orders').limit(1)
        orders = orders_ref.get()
        
        if not orders:
            print_error("Test qilish uchun order yo'q")
            return False
        
        order_id = orders[0].id
        order_data = orders[0].to_dict()
        amount = order_data.get('total', 0) * 100
        
        # Base64 encoded URL yaratish
        params = {
            "m": settings.PAYME_MERCHANT_ID,
            "ac": {"order_id": order_id},
            "a": amount
        }
        
        params_json = json.dumps(params)
        params_base64 = base64.b64encode(params_json.encode('utf-8')).decode('utf-8')
        
        base_url = "https://checkout.test.paycom.uz" if settings.DEBUG else "https://checkout.paycom.uz"
        checkout_url = f"{base_url}/{params_base64}"
        
        print_success("To'lov havolasi yaratildi:")
        print(f"\n{checkout_url}\n")
        
        return True
        
    except Exception as e:
        print_error(f"Payment link generation error: {str(e)}")
        return False


def print_next_steps():
    """Keyingi qadamlar"""
    print_header("Keyingi Qadamlar")
    
    print("""
1. Serverni ishga tushiring:
   python manage.py runserver

2. API endpoint'larni test qiling:
   POST http://localhost:8000/api/payments/create-link/
   Body: {"order_id": "ORD-TEST-001"}

3. Webhook test qiling:
   TESTING_EXAMPLES.md faylida batafsil misollar bor

4. Hujjatlarni o'qing:
   - SETUP_GUIDE.md - O'rnatish
   - PAYME_INTEGRATION_GUIDE.md - Integratsiya
   - TESTING_EXAMPLES.md - Test qilish

5. Production deploy:
   - .env faylini production qiymatlari bilan to'ldiring
   - Payme Cabinet'da webhook URL sozlang
   - Nginx + Gunicorn sozlang
    """)


def main():
    """Asosiy funksiya"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🚀 Payme Backend - Quick Start Test  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    # 1. Environment variables
    results.append(("Environment", check_environment()))
    
    # 2. Firebase connection
    results.append(("Firebase", check_firebase()))
    
    # 3. Orders collection
    results.append(("Orders Collection", check_orders_collection()))
    
    # 4. OrderService
    results.append(("OrderService", test_order_service()))
    
    # 5. Payment link generation
    results.append(("Payment Link", test_payment_link_generation()))
    
    # Summary
    print_header("Test Natijalari")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print()
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<40} {status}")
    
    print()
    print(f"Jami: {passed}/{total} test muvaffaqiyatli")
    
    if passed == total:
        print_success("\n🎉 Barcha testlar muvaffaqiyatli! Loyiha tayyor!")
        print_next_steps()
        return 0
    else:
        print_error("\n⚠️ Ba'zi testlar muvaffaqiyatsiz. Xatolarni to'g'rilang.")
        print_info("SETUP_GUIDE.md faylini o'qing va Troubleshooting bo'limiga qarang.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test to'xtatildi")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
