"""
Payme Merchant API endpointlari.
Bu faylda to'lov havolasini yaratish va webhook'larni boshqarish uchun view'lar joylashgan.
"""

import base64
import json
import logging
import time
from typing import Dict, Any

from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .authentication import payme_webhook_auth
from .constants import (
    PaymeMethod,
    PaymeError,
    PaymeURL,
    TransactionState,
    OrderStatus,
    PAYME_ACCOUNT_KEY
)
from .exceptions import PaymeException
from .services import OrderService, TransactionService
from .serializers import CreatePaymentLinkSerializer

logger = logging.getLogger(__name__)


class CreatePaymentLinkView(APIView):
    """
    Payme to'lov havolasini yaratish endpointi.
    
    Request:
        POST /api/payments/create-link/
        Body: {"order_id": "ORD-12345"}
        
    Response:
        {
            "success": true,
            "checkout_url": "https://checkout.paycom.uz/base64_encoded_params",
            "order_id": "ORD-12345",
            "amount": 172000
        }
    """
    
    @extend_schema(
        tags=['Payments'],
        operation_id='create_payment_link',
        summary='To\'lov havolasini yaratish',
        description='''
        Berilgan order uchun Payme checkout havolasini yaratadi.
        
        **Workflow:**
        1. Order ID qabul qiladi
        2. Firestore'dan orderni oladi va validatsiya qiladi
        3. Order statusini tekshiradi (pending bo'lishi kerak)
        4. Payme checkout URL'ini yaratadi (base64 encoded)
        5. Summa konvertatsiyasi: so'm → tiyin (* 100)
        
        **Order Status Validatsiyasi:**
        - ✅ `pending` - To'lov havolasi yaratiladi
        - ✅ `processing` - To'lov havolasi yaratiladi
        - ❌ `paid` - Xato: Order allaqachon to'langan
        - ❌ `cancelled` - Xato: Order bekor qilingan
        ''',
        request=CreatePaymentLinkSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                name='Success Response',
                value={
                    "success": True,
                    "checkout_url": "https://checkout.test.paycom.uz/eyJtIjogInlvdXJfbWVyY2hhbnRfaWQiLCAiYWMiOiB7Im9yZGVyX2lkIjogIk9SRC0xMjM0NSJ9LCAiYSI6IDE3MjAwMDAwfQ==",
                    "order_id": "ORD-95612789",
                    "amount": 172000,
                    "amount_tiyin": 17200000
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                name='Order Not Found',
                value={
                    "success": False,
                    "error": "Order not found"
                },
                response_only=True,
                status_codes=['404']
            ),
            OpenApiExample(
                name='Order Already Paid',
                value={
                    "success": False,
                    "error": "Order already paid"
                },
                response_only=True,
                status_codes=['400']
            ),
        ]
    )
    
    def post(self, request: Request) -> Response:
        """
        To'lov havolasini yaratadi.
        
        Args:
            request: HTTP request obyekti
            
        Returns:
            JSON response to'lov havolasi bilan
        """
        try:
            # Request ma'lumotlarini validate qilish
            serializer = CreatePaymentLinkSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "error": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Order ID'ni olish
            order_id = serializer.validated_data['order_id']
            
            # Order'ni Firestore'dan olish
            order = OrderService.get_order(order_id)
            
            if not order:
                return Response(
                    {
                        "success": False,
                        "error": "Order not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Order statusini tekshirish
            order_status = order.get('status', '')
            
            if order_status == OrderStatus.PAID:
                return Response(
                    {
                        "success": False,
                        "error": "Order already paid"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if order_status == OrderStatus.CANCELLED:
                return Response(
                    {
                        "success": False,
                        "error": "Order is cancelled"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Summa olish va tiyinga aylantirish (so'm * 100)
            amount_sum = order.get('total', 0)
            amount_tiyin = amount_sum * 100
            
            # Payme checkout URL'ini yaratish
            checkout_url = self._generate_checkout_url(
                order_id=order_id,
                amount=amount_tiyin
            )
            
            logger.info(f"Payment link created for order {order_id}, amount: {amount_sum} sum")
            
            return Response(
                {
                    "success": True,
                    "checkout_url": checkout_url,
                    "order_id": order_id,
                    "amount": amount_sum,
                    "amount_tiyin": amount_tiyin
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": "Internal server error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _generate_checkout_url(order_id: str, amount: int) -> str:
        """
        Payme checkout URL'ini yaratadi (base64 encoded).
        
        Args:
            order_id: Order identifikatori
            amount: To'lov summasi (tiyinlarda)
            
        Returns:
            To'liq checkout URL
        """
        # Payme parametrlari
        params = {
            "m": settings.PAYME_MERCHANT_ID,
            "ac": {
                PAYME_ACCOUNT_KEY: order_id
            },
            "a": amount,
            "c": f"https://your-callback-url.com/order/{order_id}"  # Callback URL (ixtiyoriy)
        }
        
        # JSON'ni base64'ga encode qilish
        params_json = json.dumps(params)
        params_base64 = base64.b64encode(params_json.encode('utf-8')).decode('utf-8')
        
        # To'liq URL yaratish
        base_url = PaymeURL.PRODUCTION if not settings.DEBUG else PaymeURL.TEST
        checkout_url = f"{base_url}/{params_base64}"
        
        return checkout_url


class PaymeWebhookView(APIView):
    """
    Payme Merchant API webhook endpointi.
    JSON-RPC 2.0 protokoli bo'yicha ishlaydi.
    
    Qo'llab-quvvatlanadigan metodlar:
    - CheckPerformTransaction
    - CreateTransaction
    - PerformTransaction
    - CancelTransaction
    - CheckTransaction
    """
    
    # MUHIM: DRF'ning auto-authentication'ini o'chirish
    # Barcha authentication decorator orqali qo'lda boshqariladi
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        tags=['Payme Webhook'],
        operation_id='payme_webhook',
        summary='Payme Merchant API Webhook',
        description='''
        Payme Merchant API JSON-RPC 2.0 webhook endpoint.
        
        **Authentication:**
        ```
        Authorization: Basic base64(Paycom:YOUR_PAYME_KEY)
        ```
        
        **Qo'llab-quvvatlanadigan metodlar:**
        
        ### 1. CheckPerformTransaction
        Order to'lov uchun tayyor ekanligini tekshiradi.
        - Order mavjudligi
        - Summa to'g'riligi
        - Order holati (pending/processing)
        
        ### 2. CreateTransaction
        Yangi tranzaksiya yaratadi va order statusini `processing`ga o'zgartiradi.
        - Idempotent (bir xil tranzaksiya ikki marta yaratilmaydi)
        - Firestore'da transactions collection'ga yoziladi
        
        ### 3. PerformTransaction
        Tranzaksiyani tasdiqlab, to'lovni amalga oshiradi.
        - Order statusini `paid`ga o'zgartiradi
        - Timeout tekshiruvi (12 soat)
        
        ### 4. CancelTransaction
        Tranzaksiyani bekor qiladi.
        - Perform'dan oldin: order statusini `pending`ga qaytaradi
        - Perform'dan keyin: order statusini `cancelled`ga o'zgartiradi
        
        ### 5. CheckTransaction
        Tranzaksiya holatini qaytaradi.
        
        **JSON-RPC 2.0 Format:**
        ```json
        {
          "jsonrpc": "2.0",
          "id": 123,
          "method": "MethodName",
          "params": {...}
        }
        ```
        ''',
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Basic Auth: base64(Paycom:YOUR_PAYME_KEY)',
                required=True,
                examples=[
                    OpenApiExample(
                        name='Example',
                        value='Basic UGF5Y29tOnlvdXJfcGF5bWVfa2V5'
                    )
                ]
            ),
        ],
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            # CheckPerformTransaction
            OpenApiExample(
                name='CheckPerformTransaction Request',
                value={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "CheckPerformTransaction",
                    "params": {
                        "amount": 17200000,
                        "account": {
                            "order_id": "ORD-95612789"
                        }
                    }
                },
                request_only=True
            ),
            OpenApiExample(
                name='CheckPerformTransaction Response',
                value={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "allow": True
                    }
                },
                response_only=True,
                status_codes=['200']
            ),
            # CreateTransaction
            OpenApiExample(
                name='CreateTransaction Request',
                value={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "CreateTransaction",
                    "params": {
                        "id": "63e31fba6c668e0419b56e11",
                        "time": 1675868094123,
                        "amount": 17200000,
                        "account": {
                            "order_id": "ORD-95612789"
                        }
                    }
                },
                request_only=True
            ),
            OpenApiExample(
                name='CreateTransaction Response',
                value={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "create_time": 1675868094123,
                        "transaction": "63e31fba6c668e0419b56e11",
                        "state": 1
                    }
                },
                response_only=True,
                status_codes=['200']
            ),
            # PerformTransaction
            OpenApiExample(
                name='PerformTransaction Request',
                value={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "PerformTransaction",
                    "params": {
                        "id": "63e31fba6c668e0419b56e11"
                    }
                },
                request_only=True
            ),
            OpenApiExample(
                name='PerformTransaction Response',
                value={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "transaction": "63e31fba6c668e0419b56e11",
                        "perform_time": 1675868194123,
                        "state": 2
                    }
                },
                response_only=True,
                status_codes=['200']
            ),
            # Error Response
            OpenApiExample(
                name='Error Response',
                value={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {
                        "code": -31050,
                        "message": "Order not found",
                        "data": "Order not found"
                    }
                },
                response_only=True,
                status_codes=['200']
            ),
        ]
    )
    
    @payme_webhook_auth
    def post(self, request: Request) -> JsonResponse:
        """
        Payme webhook so'rovlarini qayta ishlaydi.
        
        Args:
            request: HTTP request obyekti
            
        Returns:
            JSON-RPC 2.0 format javob
        """
        rpc_request = None
        try:
            # JSON parse qilish
            try:
                rpc_request = request.data
            except json.JSONDecodeError:
                return self._error_response(
                    None,
                    PaymeError.PARSE_ERROR,
                    "Invalid JSON"
                )
            
            # JSON-RPC 2.0 standart maydonlarini tekshirish
            request_id = rpc_request.get('id')
            method = rpc_request.get('method')
            params = rpc_request.get('params', {})
            
            if not method:
                return self._error_response(
                    request_id,
                    PaymeError.INVALID_REQUEST,
                    "Method is required"
                )
            
            # Metodga mos handler'ni chaqirish
            handler_map = {
                PaymeMethod.CHECK_PERFORM_TRANSACTION: self._check_perform_transaction,
                PaymeMethod.CREATE_TRANSACTION: self._create_transaction,
                PaymeMethod.PERFORM_TRANSACTION: self._perform_transaction,
                PaymeMethod.CANCEL_TRANSACTION: self._cancel_transaction,
                PaymeMethod.CHECK_TRANSACTION: self._check_transaction,
            }
            
            handler = handler_map.get(method)
            
            if not handler:
                return self._error_response(
                    request_id,
                    PaymeError.METHOD_NOT_FOUND,
                    f"Method '{method}' not found"
                )
            
            # Handler'ni chaqirish
            result = handler(params)
            
            return self._success_response(request_id, result)
            
        except PaymeException as pe:
            # PaymeException'ni to'g'ridan-to'g'ri qayta ishlash
            return self._error_response(
                rpc_request.get('id') if rpc_request else None,
                pe.code,
                pe.message
            )
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return self._error_response(
                rpc_request.get('id') if rpc_request else None,
                PaymeError.GENERAL_ERROR,
                "Internal server error"
            )
    
    def _check_perform_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        CheckPerformTransaction metodi.
        Order mavjudligi, summa va holatini tekshiradi.
        
        Args:
            params: {
                "amount": 17200000,  # tiyinlarda
                "account": {"order_id": "ORD-12345"}
            }
            
        Returns:
            {"allow": true} yoki xato
        """
        try:
            amount = params.get('amount')
            account = params.get('account', {})
            order_id = account.get(PAYME_ACCOUNT_KEY)
            
            if not order_id or not amount:
                raise ValueError("Missing required parameters")
            
            # Order'ni olish
            order = OrderService.get_order(order_id)
            
            # Validatsiya
            validation = OrderService.validate_order_for_payment(order, amount)
            
            if not validation['valid']:
                raise PaymeException(
                    validation['error_code'],
                    validation['error_message']
                )
            
            return {"allow": True}
            
        except PaymeException:
            raise
        except Exception as e:
            logger.error(f"CheckPerformTransaction error: {str(e)}")
            raise PaymeException(
                PaymeError.GENERAL_ERROR,
                "Error checking transaction"
            )
    
    def _create_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        CreateTransaction metodi.
        Yangi tranzaksiya yaratadi va order statusini yangilaydi.
        
        Args:
            params: {
                "id": "transaction_id",
                "time": 1609459200000,
                "amount": 17200000,
                "account": {"order_id": "ORD-12345"}
            }
            
        Returns:
            Transaction ma'lumotlari
        """
        try:
            transaction_id = params.get('id')
            create_time = params.get('time')
            amount = params.get('amount')
            account = params.get('account', {})
            order_id = account.get(PAYME_ACCOUNT_KEY)
            
            if not all([transaction_id, create_time, amount, order_id]):
                raise PaymeException(
                    PaymeError.INVALID_PARAMS,
                    "Missing required parameters"
                )
            
            # Tranzaksiya mavjudligini tekshirish
            existing_transaction = TransactionService.get_transaction(transaction_id)
            
            if existing_transaction:
                # Tranzaksiya allaqachon mavjud - mavjud ma'lumotni qaytarish
                return {
                    "create_time": existing_transaction['createTime'],
                    "transaction": existing_transaction['id'],
                    "state": existing_transaction['state']
                }
            
            # Order'ni validatsiya qilish
            order = OrderService.get_order(order_id)
            validation = OrderService.validate_order_for_payment(order, amount)
            
            if not validation['valid']:
                raise PaymeException(
                    validation['error_code'],
                    validation['error_message']
                )
            
            # Yangi tranzaksiya yaratish
            transaction = TransactionService.create_transaction(
                transaction_id=transaction_id,
                order_id=order_id,
                amount=amount,
                create_time=create_time,
                account=account
            )
            
            # Order statusini yangilash
            OrderService.update_order_status(
                order_id=order_id,
                status=OrderStatus.PROCESSING,
                transaction_id=transaction_id
            )
            
            return {
                "create_time": transaction['createTime'],
                "transaction": transaction['id'],
                "state": transaction['state']
            }
            
        except PaymeException:
            raise
        except Exception as e:
            logger.error(f"CreateTransaction error: {str(e)}", exc_info=True)
            raise PaymeException(
                PaymeError.GENERAL_ERROR,
                "Error creating transaction"
            )
    
    def _perform_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        PerformTransaction metodi.
        Tranzaksiyani tasdiqlab, to'lovni amalga oshiradi.
        
        Args:
            params: {"id": "transaction_id"}
            
        Returns:
            Transaction holati
        """
        try:
            transaction_id = params.get('id')
            
            if not transaction_id:
                raise PaymeException(
                    PaymeError.INVALID_PARAMS,
                    "Transaction id is required"
                )
            
            # Tranzaksiyani olish
            transaction = TransactionService.get_transaction(transaction_id)
            
            if not transaction:
                raise PaymeException(
                    PaymeError.TRANSACTION_NOT_FOUND,
                    "Transaction not found"
                )
            
            # Agar allaqachon tasdiqlanган bo'lsa
            if transaction['state'] == TransactionState.COMPLETED:
                return {
                    "transaction": transaction['id'],
                    "perform_time": transaction['performTime'],
                    "state": transaction['state']
                }
            
            # Agar bekor qilingan bo'lsa
            if transaction['state'] in [TransactionState.CANCELLED, TransactionState.CANCELLED_AFTER_COMPLETE]:
                raise PaymeException(
                    PaymeError.TRANSACTION_ALREADY_CANCELLED,
                    "Transaction is cancelled"
                )
            
            # Timeout tekshiruvi
            if not TransactionService.validate_transaction_timeout(transaction['createTime']):
                # Timeout bo'lgan tranzaksiyani bekor qilish
                current_time = int(time.time() * 1000)
                TransactionService.cancel_transaction(
                    transaction_id=transaction_id,
                    cancel_time=current_time,
                    reason=4  # Timeout
                )
                raise PaymeException(
                    PaymeError.TRANSACTION_CANNOT_BE_CANCELLED,
                    "Transaction timeout expired"
                )
            
            # Tranzaksiyani tasdiqash
            perform_time = int(time.time() * 1000)
            TransactionService.perform_transaction(
                transaction_id=transaction_id,
                perform_time=perform_time
            )
            
            # Order statusini 'paid' ga o'zgartirish
            order_id = transaction['orderId']
            OrderService.update_order_status(
                order_id=order_id,
                status=OrderStatus.PAID
            )
            
            return {
                "transaction": transaction_id,
                "perform_time": perform_time,
                "state": TransactionState.COMPLETED
            }
            
        except PaymeException:
            raise
        except Exception as e:
            logger.error(f"PerformTransaction error: {str(e)}", exc_info=True)
            raise PaymeException(
                PaymeError.GENERAL_ERROR,
                "Error performing transaction"
            )
    
    def _cancel_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        CancelTransaction metodi.
        Tranzaksiyani bekor qiladi va order holatini tiklaydi.
        
        Args:
            params: {
                "id": "transaction_id",
                "reason": 1  # 1-5 orasida
            }
            
        Returns:
            Transaction holati
        """
        try:
            transaction_id = params.get('id')
            reason = params.get('reason')
            
            if not transaction_id or reason is None:
                raise PaymeException(
                    PaymeError.INVALID_PARAMS,
                    "Transaction id and reason are required"
                )
            
            # Tranzaksiyani olish
            transaction = TransactionService.get_transaction(transaction_id)
            
            if not transaction:
                raise PaymeException(
                    PaymeError.TRANSACTION_NOT_FOUND,
                    "Transaction not found"
                )
            
            # Agar allaqachon bekor qilingan bo'lsa
            if transaction['state'] in [TransactionState.CANCELLED, TransactionState.CANCELLED_AFTER_COMPLETE]:
                return {
                    "transaction": transaction['id'],
                    "cancel_time": transaction['cancelTime'],
                    "state": transaction['state']
                }
            
            # Tranzaksiyani bekor qilish
            cancel_time = int(time.time() * 1000)
            TransactionService.cancel_transaction(
                transaction_id=transaction_id,
                cancel_time=cancel_time,
                reason=reason
            )
            
            # Order statusini tiklash
            order_id = transaction['orderId']
            new_status = OrderStatus.CANCELLED if transaction['state'] == TransactionState.COMPLETED else OrderStatus.PENDING
            OrderService.update_order_status(
                order_id=order_id,
                status=new_status
            )
            
            # Yangi state'ni aniqlash
            new_state = TransactionState.CANCELLED_AFTER_COMPLETE if transaction['state'] == TransactionState.COMPLETED else TransactionState.CANCELLED
            
            return {
                "transaction": transaction_id,
                "cancel_time": cancel_time,
                "state": new_state
            }
            
        except PaymeException:
            raise
        except Exception as e:
            logger.error(f"CancelTransaction error: {str(e)}", exc_info=True)
            raise PaymeException(
                PaymeError.GENERAL_ERROR,
                "Error cancelling transaction"
            )
    
    def _check_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        CheckTransaction metodi.
        Tranzaksiya holatini qaytaradi.
        
        Args:
            params: {"id": "transaction_id"}
            
        Returns:
            To'liq transaction ma'lumotlari
        """
        try:
            transaction_id = params.get('id')
            
            if not transaction_id:
                raise PaymeException(
                    PaymeError.INVALID_PARAMS,
                    "Transaction id is required"
                )
            
            # Tranzaksiyani olish
            transaction = TransactionService.get_transaction(transaction_id)
            
            if not transaction:
                raise PaymeException(
                    PaymeError.TRANSACTION_NOT_FOUND,
                    "Transaction not found"
                )
            
            return {
                "create_time": transaction['createTime'],
                "perform_time": transaction.get('performTime', 0),
                "cancel_time": transaction.get('cancelTime', 0),
                "transaction": transaction['id'],
                "state": transaction['state'],
                "reason": transaction.get('reason')
            }
            
        except PaymeException:
            raise
        except Exception as e:
            logger.error(f"CheckTransaction error: {str(e)}", exc_info=True)
            raise PaymeException(
                PaymeError.GENERAL_ERROR,
                "Error checking transaction"
            )
    
    @staticmethod
    def _success_response(request_id: Any, result: Dict[str, Any]) -> JsonResponse:
        """
        JSON-RPC 2.0 muvaffaqiyatli javob yaratadi.
        
        Args:
            request_id: So'rov ID'si
            result: Natija ma'lumotlari
            
        Returns:
            JSON response
        """
        return JsonResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
    
    @staticmethod
    @staticmethod
    def _error_response(request_id: Any, code: int, message: str, 
                       data: Any = None) -> JsonResponse:
        """
        JSON-RPC 2.0 xato javobi yaratadi.
        Payme protokoliga muvofiq 3 tilda xato xabarini qaytaradi.
        
        Args:
            request_id: So'rov ID'si
            code: Xato kodi (PaymeError.* konstantalaridan)
            message: Qo'shimcha xato xabari (data field uchun)
            data: Qo'shimcha ma'lumotlar (ixtiyoriy, agar berilmasa message ishlatiladi)
            
        Returns:
            JSON response (har doim HTTP 200 status bilan)
        """
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
        }, status=200)  # MUHIM: Har doim HTTP 200 qaytarish kerak!

