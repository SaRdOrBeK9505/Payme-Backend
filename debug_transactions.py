#!/usr/bin/env python
"""
Tranzaksiyalarni debug qilish uchun skript.
"""

import os
import django
import sys

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.firebase_config import db
from payments.constants import FirestoreCollection, TransactionState

def list_all_transactions():
    """Barcha tranzaksiyalarni ko'rsatadi."""
    print("\n" + "="*80)
    print("FIRESTORE'DAGI BARCHA TRANZAKSIYALAR")
    print("="*80 + "\n")
    
    try:
        transactions_ref = db.collection(FirestoreCollection.TRANSACTIONS)
        transactions = transactions_ref.stream()
        
        count = 0
        for doc in transactions:
            count += 1
            txn = doc.to_dict()
            
            state_name = {
                1: "CREATED (pending)",
                2: "COMPLETED",
                -1: "CANCELLED",
                -2: "CANCELLED_AFTER_COMPLETE"
            }.get(txn.get('state'), f"UNKNOWN ({txn.get('state')})")
            
            print(f"💳 Tranzaksiya #{count}")
            print(f"   ID:                {doc.id}")
            print(f"   Order ID:          {txn.get('orderId', 'N/A')}")
            print(f"   State:             {state_name}")
            print(f"   Amount (tiyin):    {txn.get('amount', 0)}")
            print(f"   Create Time:       {txn.get('createTime', 'N/A')}")
            print(f"   Perform Time:      {txn.get('performTime', 'N/A')}")
            print(f"   Cancel Time:       {txn.get('cancelTime', 'N/A')}")
            print("-" * 80)
        
        if count == 0:
            print("❌ Hech qanday tranzaksiya topilmadi!")
        else:
            print(f"✅ Jami: {count} ta tranzaksiya topildi")
        
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80 + "\n")


def find_transaction_by_id(txn_id: str):
    """ID bo'yicha tranzaksiyani topadi."""
    print(f"\n🔍 Tranzaksiya qidirilmoqda: {txn_id}\n")
    
    try:
        doc_ref = db.collection(FirestoreCollection.TRANSACTIONS).document(txn_id)
        doc = doc_ref.get()
        
        if doc.exists:
            txn = doc.to_dict()
            print("✅ Topildi!")
            print(f"   Order ID:     {txn.get('orderId')}")
            print(f"   State:        {txn.get('state')}")
            print(f"   Amount:       {txn.get('amount')}")
            print(f"   Create Time:  {txn.get('createTime')}")
        else:
            print("❌ Tranzaksiya topilmadi!")
    
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()


def find_pending_for_order(order_id: str):
    """Order uchun pending tranzaksiyalarni topadi."""
    print(f"\n🔍 Order uchun pending tranzaksiyalar: {order_id}\n")
    
    try:
        transactions_ref = db.collection(FirestoreCollection.TRANSACTIONS)
        query = transactions_ref.where('orderId', '==', order_id).where('state', '==', TransactionState.CREATED)
        results = query.stream()
        
        count = 0
        for doc in results:
            count += 1
            txn = doc.to_dict()
            print(f"   {count}. ID: {doc.id}")
            print(f"      Amount: {txn.get('amount')}")
            print(f"      Create Time: {txn.get('createTime')}")
        
        if count == 0:
            print("   ✅ Pending tranzaksiya yo'q")
        else:
            print(f"\n   ⚠️  Jami {count} ta pending tranzaksiya topildi!")
    
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()


def clear_all_transactions():
    """BARCHA tranzaksiyalarni o'chiradi (EHTIYOT!)"""
    confirm = input("\n⚠️  DIQQAT: Barcha tranzaksiyalarni o'chirasizmi? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Bekor qilindi")
        return
    
    print("\n🗑️  Tranzaksiyalar o'chirilmoqda...")
    
    try:
        transactions_ref = db.collection(FirestoreCollection.TRANSACTIONS)
        transactions = transactions_ref.stream()
        
        count = 0
        for doc in transactions:
            doc.reference.delete()
            count += 1
            print(f"   ✅ O'chirildi: {doc.id}")
        
        print(f"\n✅ Jami {count} ta tranzaksiya o'chirildi\n")
    
    except Exception as e:
        print(f"❌ Xato: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_all_transactions()
        
        elif command == "find" and len(sys.argv) > 2:
            find_transaction_by_id(sys.argv[2])
        
        elif command == "pending" and len(sys.argv) > 2:
            find_pending_for_order(sys.argv[2])
        
        elif command == "clear":
            clear_all_transactions()
        
        else:
            print("Noto'g'ri buyruq!")
            print("\nFoydalanish:")
            print("  python debug_transactions.py list")
            print("  python debug_transactions.py find <transaction_id>")
            print("  python debug_transactions.py pending <order_id>")
            print("  python debug_transactions.py clear")
    
    else:
        print("\n📋 MENYUDAN TANLANG:\n")
        print("1. Barcha tranzaksiyalarni ko'rsatish")
        print("2. ID bo'yicha qidirish")
        print("3. Order uchun pending tranzaksiyalarni topish")
        print("4. Barcha tranzaksiyalarni o'chirish")
        print("0. Chiqish\n")
        
        choice = input("Tanlov (0-4): ")
        
        if choice == "1":
            list_all_transactions()
        elif choice == "2":
            txn_id = input("Transaction ID: ")
            find_transaction_by_id(txn_id)
        elif choice == "3":
            order_id = input("Order ID: ")
            find_pending_for_order(order_id)
        elif choice == "4":
            clear_all_transactions()
        elif choice == "0":
            print("Xayr!")
        else:
            print("Noto'g'ri tanlov!")
