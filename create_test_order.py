#!/usr/bin/env python
"""
Test uchun Firestore'ga order yaratish skripti.
"""

import os
import django
import random

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from core.firebase_config import db
from payments.constants import FirestoreCollection, OrderStatus

def create_test_order(total_amount=1720):
    """
    Test uchun order yaratadi.
    
    Args:
        total_amount: Order summasi (so'mda)
    """
    print("\n" + "="*60)
    print("TEST ORDER YARATISH")
    print("="*60 + "\n")
    
    try:
        # Order ID generatsiya qilish
        order_id = f"ORD-{random.randint(10000000, 99999999)}"
        
        # Order ma'lumotlari
        order_data = {
            'status': OrderStatus.PENDING,
            'total': total_amount,
            'currency': 'UZS',
            'description': f'Test order - {order_id}',
            'createdAt': SERVER_TIMESTAMP,
            'updatedAt': SERVER_TIMESTAMP,
        }
        
        # Firestore'ga yozish
        doc_ref = db.collection(FirestoreCollection.ORDERS).document(order_id)
        doc_ref.set(order_data)
        
        print(f"✅ Order muvaffaqiyatli yaratildi!")
        print(f"\n📦 Order Ma'lumotlari:")
        print(f"   Order ID (order_id):  {order_id}")
        print(f"   Status:               {OrderStatus.PENDING}")
        print(f"   Total (so'm):         {total_amount}")
        print(f"   Total (tiyin):        {total_amount * 100}")
        
        print(f"\n🔗 To'lov havolasini olish uchun:")
        print(f"   curl -X POST http://localhost:8000/api/payments/create-link/ \\")
        print(f"     -H \"Content-Type: application/json\" \\")
        print(f"     -d '{{\"order_id\": \"{order_id}\"}}'")
        
        print(f"\n🧪 Payme webhook test qilish uchun:")
        print(f"   Order ID: {order_id}")
        print(f"   Amount (tiyin): {total_amount * 100}")
        
        return order_id
        
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    # Agar command line'dan summa berilgan bo'lsa
    if len(sys.argv) > 1:
        try:
            amount = int(sys.argv[1])
            create_test_order(amount)
        except ValueError:
            print("❌ Summa raqam bo'lishi kerak!")
            print("Misol: python create_test_order.py 5000")
    else:
        # Default summa - 1720 so'm
        create_test_order()
