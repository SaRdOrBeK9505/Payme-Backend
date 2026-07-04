"""
Payme va Firestore bilan ishlash uchun biznes logika.
Bu faylda orderlar va tranzaksiyalar bilan bog'liq barcha CRUD operatsiyalar amalga oshiriladi.
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from google.cloud import firestore
from google.api_core.exceptions import NotFound, AlreadyExists

from core.firebase_config import db
from .constants import (
    FirestoreCollection,
    OrderStatus,
    TransactionState,
    PaymeError,
    PaymeTimeout
)

logger = logging.getLogger(__name__)


class OrderService:
    """
    Order'lar bilan ishlash uchun xizmat klassi.
    Firestore'da orders collection'i bilan o'zaro aloqani ta'minlaydi.
    """
    
    @staticmethod
    def get_order(order_id: str) -> Optional[Dict[str, Any]]:
        """
        Order'ni ID bo'yicha oladi.
        
        Args:
            order_id: Order identifikatori (masalan: "ORD-95612789")
            
        Returns:
            Order ma'lumotlari yoki None (agar topilmasa)
        """
        try:
            doc_ref = db.collection(FirestoreCollection.ORDERS).document(order_id)
            doc = doc_ref.get()
            
            if doc.exists:
                order_data = doc.to_dict()
                order_data['id'] = doc.id
                return order_data
            
            logger.warning(f"Order not found: {order_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            raise
    
    @staticmethod
    def update_order_status(order_id: str, status: str, 
                           transaction_id: Optional[str] = None) -> bool:
        """
        Order statusini yangilaydi.
        
        Args:
            order_id: Order identifikatori
            status: Yangi status (OrderStatus enum'dan)
            transaction_id: Payme tranzaksiya ID'si (ixtiyoriy)
            
        Returns:
            True agar yangilash muvaffaqiyatli bo'lsa
        """
        try:
            doc_ref = db.collection(FirestoreCollection.ORDERS).document(order_id)
            
            update_data = {
                'status': status,
                'updatedAt': SERVER_TIMESTAMP
            }
            
            if transaction_id:
                update_data['paymeTransactionId'] = transaction_id
            
            # Agar to'lov muvaffaqiyatli bo'lsa, paidAt maydonini qo'shish
            if status == OrderStatus.PAID:
                update_data['paidAt'] = SERVER_TIMESTAMP
            
            doc_ref.update(update_data)
            logger.info(f"Order {order_id} status updated to {status}")
            return True
            
        except NotFound:
            logger.error(f"Order not found during update: {order_id}")
            raise
        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {str(e)}")
            raise
    
    @staticmethod
    def validate_order_for_payment(order: Optional[Dict[str, Any]], amount: int) -> Dict[str, Any]:
        """
        Order'ni to'lov uchun validatsiya qiladi.
        
        Args:
            order: Order ma'lumotlari
            amount: To'lov summasi (tiyinlarda)
            
        Returns:
            Validatsiya natijasi: {"valid": bool, "error_code": int, "error_message": str}
        """
        # Order mavjudligini tekshirish
        if not order:
            return {
                "valid": False,
                "error_code": PaymeError.ORDER_NOT_FOUND,
                "error_message": "Order not found"
            }
        
        # Order statusini tekshirish
        order_status = order.get('status', '')
        
        if order_status == OrderStatus.PAID:
            return {
                "valid": False,
                "error_code": PaymeError.ORDER_ALREADY_PAID,
                "error_message": "Order already paid"
            }
        
        if order_status == OrderStatus.CANCELLED:
            return {
                "valid": False,
                "error_code": PaymeError.ORDER_CANCELLED,
                "error_message": "Order is cancelled"
            }
        
        # Summa to'g'riligini tekshirish (so'mdan tiyinga: * 100)
        expected_amount = order.get('total', 0) * 100
        
        if amount != expected_amount:
            return {
                "valid": False,
                "error_code": PaymeError.INCORRECT_AMOUNT,
                "error_message": f"Incorrect amount. Expected: {expected_amount}, got: {amount}"
            }
        
        return {"valid": True}


class TransactionService:
    """
    Payme tranzaksiyalari bilan ishlash uchun xizmat klassi.
    Firestore'da transactions collection'i bilan o'zaro aloqani ta'minlaydi.
    """
    
    @staticmethod
    def create_transaction(transaction_id: str, order_id: str, amount: int, 
                          create_time: int, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yangi tranzaksiya yaratadi.
        
        Firestore transaction'dan foydalanib race condition'dan himoyalanadi.
        Bu idempotent operation - bir xil tranzaksiya ikki marta yaratilmaydi.
        
        Args:
            transaction_id: Payme tranzaksiya ID'si
            order_id: Order identifikatori
            amount: To'lov summasi (tiyinlarda)
            create_time: Yaratilgan vaqt (Unix timestamp, milliseconds)
            account: Payme account ma'lumotlari
            
        Returns:
            Yaratilgan tranzaksiya ma'lumotlari
        """
        try:
            transaction_data = {
                'id': transaction_id,
                'orderId': order_id,
                'amount': amount,
                'state': TransactionState.CREATED,
                'createTime': create_time,
                'performTime': None,
                'cancelTime': None,
                'reason': None,
                'account': account,
                'createdAt': SERVER_TIMESTAMP,
                'updatedAt': SERVER_TIMESTAMP
            }
            
            # Firestore transaction bilan atomic operation
            @firestore.transactional
            def create_in_transaction(transaction, doc_ref):
                """
                Tranzaksiyani atomic ravishda yaratadi.
                Agar allaqachon mavjud bo'lsa, mavjud ma'lumotni qaytaradi.
                """
                snapshot = doc_ref.get(transaction=transaction)
                if snapshot.exists:
                    # Tranzaksiya allaqachon mavjud - mavjud ma'lumotni qaytarish
                    logger.info(f"Transaction already exists: {transaction_id}")
                    return snapshot.to_dict()
                
                # Yangi tranzaksiyani yaratish
                transaction.set(doc_ref, transaction_data)
                logger.info(f"Transaction created: {transaction_id} for order {order_id}")
                return transaction_data
            
            # Firestore transaction'ni boshlash
            db_transaction = db.transaction()
            doc_ref = db.collection(FirestoreCollection.TRANSACTIONS).document(transaction_id)
            result = create_in_transaction(db_transaction, doc_ref)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating transaction {transaction_id}: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Tranzaksiyani ID bo'yicha oladi.
        
        Args:
            transaction_id: Payme tranzaksiya ID'si
            
        Returns:
            Tranzaksiya ma'lumotlari yoki None (agar topilmasa)
        """
        try:
            doc_ref = db.collection(FirestoreCollection.TRANSACTIONS).document(transaction_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            
            logger.warning(f"Transaction not found: {transaction_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_transaction_by_order(order_id: str) -> Optional[Dict[str, Any]]:
        """
        Order ID bo'yicha tranzaksiyani qidiradi.
        
        Args:
            order_id: Order identifikatori
            
        Returns:
            Tranzaksiya ma'lumotlari yoki None (agar topilmasa)
        """
        try:
            transactions_ref = db.collection(FirestoreCollection.TRANSACTIONS)
            query = transactions_ref.where('orderId', '==', order_id).limit(1)
            results = query.stream()
            
            for doc in results:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting transaction by order {order_id}: {str(e)}")
            raise
    
    @staticmethod
    def perform_transaction(transaction_id: str, perform_time: int) -> bool:
        """
        Tranzaksiyani tasdiqlab, to'lovni amalga oshiradi.
        
        Args:
            transaction_id: Payme tranzaksiya ID'si
            perform_time: Tasdiqlanish vaqti (Unix timestamp, milliseconds)
            
        Returns:
            True agar muvaffaqiyatli bo'lsa
        """
        try:
            doc_ref = db.collection(FirestoreCollection.TRANSACTIONS).document(transaction_id)
            doc_ref.update({
                'state': TransactionState.COMPLETED,
                'performTime': perform_time,
                'updatedAt': SERVER_TIMESTAMP
            })
            
            logger.info(f"Transaction performed: {transaction_id}")
            return True
            
        except NotFound:
            logger.error(f"Transaction not found during perform: {transaction_id}")
            raise
        except Exception as e:
            logger.error(f"Error performing transaction {transaction_id}: {str(e)}")
            raise
    
    @staticmethod
    def cancel_transaction(transaction_id: str, cancel_time: int, reason: int) -> bool:
        """
        Tranzaksiyani bekor qiladi.
        
        Args:
            transaction_id: Payme tranzaksiya ID'si
            cancel_time: Bekor qilinish vaqti (Unix timestamp, milliseconds)
            reason: Bekor qilish sababi (1-5)
            
        Returns:
            True agar muvaffaqiyatli bo'lsa
        """
        try:
            transaction = TransactionService.get_transaction(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction not found: {transaction_id}")
            
            # State'ni aniqlash (perform qilinganmi yo'qmi)
            current_state = transaction.get('state')
            new_state = (TransactionState.CANCELLED_AFTER_COMPLETE 
                        if current_state == TransactionState.COMPLETED 
                        else TransactionState.CANCELLED)
            
            doc_ref = db.collection(FirestoreCollection.TRANSACTIONS).document(transaction_id)
            doc_ref.update({
                'state': new_state,
                'cancelTime': cancel_time,
                'reason': reason,
                'updatedAt': SERVER_TIMESTAMP
            })
            
            logger.info(f"Transaction cancelled: {transaction_id}, reason: {reason}")
            return True
            
        except NotFound:
            logger.error(f"Transaction not found during cancel: {transaction_id}")
            raise
        except Exception as e:
            logger.error(f"Error cancelling transaction {transaction_id}: {str(e)}")
            raise
    
    @staticmethod
    def validate_transaction_timeout(create_time: int, current_time: Optional[int] = None) -> bool:
        """
        Tranzaksiya timeout muddatini tekshiradi.
        
        Payme'da tranzaksiya yaratilgandan keyin 12 soat (43200000 ms) ichida 
        PerformTransaction chaqirilishi kerak.
        
        Args:
            create_time: Tranzaksiya yaratilgan vaqt (milliseconds)
            current_time: Hozirgi vaqt (milliseconds), agar berilmasa hozirgi vaqt ishlatiladi
            
        Returns:
            True agar timeout muddat ichida bo'lsa, False aks holda
        """
        if current_time is None:
            current_time = int(time.time() * 1000)
        
        elapsed_time = current_time - create_time
        is_valid = elapsed_time <= PaymeTimeout.CREATE_TRANSACTION
        
        if not is_valid:
            logger.warning(
                f"Transaction timeout exceeded. Created: {create_time}, "
                f"Current: {current_time}, Elapsed: {elapsed_time}ms"
            )
        
        return is_valid
