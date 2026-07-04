"""
Payments app uchun serializer'lar.
DRF validation va data formatting uchun ishlatiladi.
"""

import re
from rest_framework import serializers


class CreatePaymentLinkSerializer(serializers.Serializer):
    """
    To'lov havolasini yaratish uchun serializer.
    """
    order_id = serializers.CharField(
        required=True,
        max_length=100,
        min_length=3,
        help_text="Order identifikatori (masalan: ORD-95612789)"
    )
    
    def validate_order_id(self, value):
        """
        Order ID formatini tekshirish.
        
        Qoidalar:
        - Bo'sh bo'lmasligi kerak
        - Kamida 3 belgidan iborat bo'lishi kerak
        - Faqat harf, raqam, tire va pastki chiziq ishlatilishi mumkin
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Order ID bo'sh bo'lishi mumkin emas")
        
        value = value.strip()
        
        # Format tekshiruvi: faqat harf, raqam, tire va pastki chiziq
        if not re.match(r'^[A-Za-z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Order ID faqat harflar, raqamlar, tire (-) va pastki chiziq (_) dan iborat bo'lishi kerak"
            )
        
        return value


class PaymentLinkResponseSerializer(serializers.Serializer):
    """
    To'lov havolasi javobi uchun serializer.
    """
    success = serializers.BooleanField()
    checkout_url = serializers.URLField(required=False)
    order_id = serializers.CharField(required=False)
    amount = serializers.IntegerField(required=False)
    amount_tiyin = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)
