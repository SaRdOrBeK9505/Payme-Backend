#!/usr/bin/env python
"""
Pending tranzaksiyalarni bekor qilish uchun skript.
"""

import os
import django
import time

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.firebase_config import db
from payments.constants import FirestoreCollection, TransactionState
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

def cancel_all_pending_transactions():
    """
    Barcha pending (state=1) tranzaksiyalarni bekor qiladi.
    """
    print("\n" + "="*80)
    print("PENDING TRANZAKSIYALARNI BEKOR QILISH")
    print("="*80 + "\n")
    
    try:
        transactions_ref = db.collection(FirestoreCollection.TRANSACTIONS)
        query = transactions_ref.where('state', '==', TransactionState.CREATED)
        pending_transactions = query.stream()
        
        count = 0
        cancel_time = int(time.time() * 1000)
        
        for doc in pending_transactions:
            count += 1
            txn = doc.to_dict()
            
            print(f"🔄 Bekor qilinmoqda #{count}:")
            print(f"   ID:        {doc.id}")
            print(f"   Order ID:  {txn.get('orderId')}")
            print(f"   Amount:    {txn.get('amount')}")
            
            # Tranzaksiyani bekor qilish
            doc.reference.update({
                'state': TransactionState.CANCELLED,
                'cancelTime': cancel_time,
                'reason': 5,  # Administratively cancelled
                'updatedAt': SERVER_TIMESTAMP
            })
            
            print(f"   ✅ Bekor qilindi!\n")
        
        if count == 0:
            print("✅ Pending tranzaksiya topilmadi (hammasi toza)")
        else:
            print(f"✅ Jami {count} ta pending tranzaksiya bekor qilindi")
        
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    confirm = input("⚠️  Barcha pending tranzaksiyalarni bekor qilasizmi? (yes/no): ")
    
    if confirm.lower() == 'yes':
        cancel_all_pending_transactions()
    else:
        print("\n❌ Bekor qilindi. Hech narsa o'zgarmadi.\n")
