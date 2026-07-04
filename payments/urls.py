"""
Payments app URL konfiguratsiyasi.
"""

from django.urls import path
from .views import CreatePaymentLinkView, PaymeWebhookView

app_name = 'payments'

urlpatterns = [
    # To'lov havolasini yaratish endpointi
    path('create-link/', CreatePaymentLinkView.as_view(), name='create-payment-link'),
    
    # Payme webhook (Merchant API)
    path('webhook/', PaymeWebhookView.as_view(), name='payme-webhook'),
]
