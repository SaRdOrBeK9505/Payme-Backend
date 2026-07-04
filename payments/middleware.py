"""
Payments app uchun custom middleware'lar.
"""

import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PaymeRequestLoggingMiddleware(MiddlewareMixin):
    """
    Payme webhook so'rovlarini loglash uchun middleware.
    Faqat /api/payments/webhook/ endpointiga kelgan so'rovlarni loglaydi.
    """
    
    def process_request(self, request):
        """
        Kiruvchi so'rovni loglaydi.
        """
        if request.path == '/api/payments/webhook/':
            logger.info(
                f"Payme Webhook Request - "
                f"Method: {request.method}, "
                f"IP: {self.get_client_ip(request)}, "
                f"Content-Type: {request.content_type}"
            )
        return None
    
    def process_response(self, request, response):
        """
        Javobni loglaydi.
        """
        if request.path == '/api/payments/webhook/':
            logger.info(
                f"Payme Webhook Response - "
                f"Status: {response.status_code}"
            )
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Client IP manzilini oladi."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
