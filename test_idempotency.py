#!/usr/bin/env python
"""
CheckTransaction idempotentligini tekshirish uchun test skript.
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from payments.services import TransactionService

def test_check_transaction_idempotency(transaction_id: str):
    """
    CheckTransaction metodining idempotentligini tekshiradi.
    """
    print("\n" + "="*80)
    print(f"IDEMPOTENTLIK TESTI: {transaction_id}")
    print("="*80 + "\n")
    
    results = []
    
    for i in range(3):
        print(f"🔄 Chaqiruv #{i+1}:")
        
        # Tranzaksiyani olish (CheckTransaction mantiq'i)
        transaction = TransactionService.get_transaction(transaction_id)
        
        if not transaction:
            print("   ❌ Tranzaksiya topilmadi!\n")
            return
        
        # CheckTransaction javobini yaratish
        result = {
            "create_time": transaction['createTime'],
            "perform_time": transaction.get('performTime', 0),
            "cancel_time": transaction.get('cancelTime', 0),
            "transaction": transaction['id'],
            "state": transaction['state'],
            "reason": transaction.get('reason')
        }
        
        results.append(result)
        
        print(f"   create_time:  {result['create_time']}")
        print(f"   perform_time: {result['perform_time']}")
        print(f"   state:        {result['state']}")
        print()
    
    # Barcha natijalarni solishturish
    print("📊 TAQQOSLASH:")
    print("-" * 80)
    
    all_same = True
    for i in range(1, len(results)):
        if results[i] != results[0]:
            all_same = False
            print(f"❌ Chaqiruv #{i+1} chaqiruv #1'dan farq qiladi!")
            print(f"   Chaqiruv #1: {json.dumps(results[0], indent=2)}")
            print(f"   Chaqiruv #{i+1}: {json.dumps(results[i], indent=2)}")
        else:
            print(f"✅ Chaqiruv #{i+1} chaqiruv #1 bilan bir xil")
    
    print("-" * 80)
    
    if all_same:
        print("\n✅ IDEMPOTENTLIK TEST O'TDI! Barcha chaqiruvlar bir xil natija qaytardi.\n")
    else:
        print("\n❌ IDEMPOTENTLIK TESTI MUVAFFAQIYATSIZ! Natijalar farq qilmoqda.\n")
        print("🔍 FIRESTORE'DAGI TO'LIQ MA'LUMOT:")
        print(json.dumps(transaction, indent=2, default=str))
    
    print("="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        txn_id = sys.argv[1]
        test_check_transaction_idempotency(txn_id)
    else:
        print("\n📋 Foydalanish:")
        print("   python test_idempotency.py <transaction_id>")
        print("\nMisol:")
        print("   python test_idempotency.py 6a4bdadc08c0938ac2d1f0cc")
        print()
