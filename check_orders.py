#!/usr/bin/env python
"""
Firestore'dagi barcha orderlarni ko'rish uchun yordamchi skript.
"""

import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.firebase_config import db
from payments.constants import FirestoreCollection

def list_orders():
    """Firestore'dagi barcha orderlarni ko'rsatadi."""
    print("\n" + "="*60)
    print("FIRESTORE'DAGI ORDERLAR")
    print("="*60 + "\n")
    
    try:
        orders_ref = db.collection(FirestoreCollection.ORDERS)
        orders = orders_ref.stream()
        
        count = 0
        for doc in orders:
            count += 1
            order = doc.to_dict()
            
            print(f"📦 Order #{count}")
            print(f"   ID (order_id):     {doc.id}")
            print(f"   Status:            {order.get('status', 'N/A')}")
            print(f"   Total (so'm):      {order.get('total', 0)}")
            print(f"   Total (tiyin):     {order.get('total', 0) * 100}")
            print(f"   Created:           {order.get('createdAt', 'N/A')}")
            print(f"   Transaction ID:    {order.get('paymeTransactionId', 'N/A')}")
            print("-" * 60)
        
        if count == 0:
            print("❌ Hech qanday order topilmadi!")
            print("\nOrder yaratish uchun:")
            print("   python create_test_order.py")
        else:
            print(f"✅ Jami: {count} ta order topildi")
        
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    list_orders()
