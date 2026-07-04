"""
Payme Merchant API uchun autentifikatsiya va xavfsizlik tekshiruvlari.
Bu faylda Basic Auth va IP whitelist tekshiruvlari amalga oshiriladi.
"""

import base64
import logging
from typing import Optional, Tuple
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from rest_framework.request import Request

from .constants import PaymeError

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Clientning IP manzilini aniqlaydi (proxy orqali ham).
    
    Args:
        request: Django HTTP request obyekti
        
    Returns:
        Client IP manzili
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_basic_auth(auth_header: str) -> Optional[Tuple[str, str]]:
    """
    Basic Auth header'ni parse qiladi.
    
    Args:
        auth_header: Authorization header qiymati
        
    Returns:
        (username, password) tuple yoki None (agar parse qilish muvaffaqiyatsiz bo'lsa)
    """
    try:
        # "Basic base64_string" formatini parse qilish
        if not auth_header.startswith('Basic '):
            return None
            
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
        return (username, password)
    except Exception as e:
        logger.error(f"Basic auth parse error: {str(e)}")
        return None


def verify_payme_credentials(username: str, password: str) -> bool:
    """
    Payme authentication ma'lumotlarini tekshiradi.
    
    Expected format: username = "Paycom", password = PAYME_KEY
    
    Args:
        username: Basic auth username
        password: Basic auth password (Payme KEY)
        
    Returns:
        True agar ma'lumotlar to'g'ri bo'lsa, aks holda False
    """
    expected_username = "Paycom"
    expected_password = settings.PAYME_KEY
    
    if not expected_password:
        logger.error("PAYME_KEY is not configured in settings")
        return False
    
    return username == expected_username and password == expected_password


def check_ip_whitelist(request: Request) -> bool:
    """
    Client IP manzilini whitelist bilan solishtiradi.
    
    Args:
        request: Django HTTP request obyekti
        
    Returns:
        True agar IP whitelist'da bo'lsa yoki whitelist bo'sh bo'lsa, aks holda False
    """
    allowed_ips = settings.PAYME_ALLOWED_IPS
    
    # Agar whitelist bo'sh bo'lsa yoki birinchi element bo'sh bo'lsa, barcha IP'larga ruxsat
    if not allowed_ips or not allowed_ips[0]:
        return True
    
    client_ip = get_client_ip(request)
    
    if client_ip in allowed_ips:
        return True
    
    logger.warning(f"IP not in whitelist: {client_ip}")
    return False


def payme_webhook_auth(view_func):
    """
    Payme webhook endpointlari uchun autentifikatsiya decorator'i.
    
    Bu decorator quyidagilarni tekshiradi:
    1. Basic Auth credentials (Paycom:PAYME_KEY)
    2. IP whitelist (agar settings'da belgilangan bo'lsa)
    
    MUHIM: Payme Merchant API protokoli bo'yicha, barcha javoblar
    HTTP 200 status kodi bilan qaytarilishi kerak. Xatolar faqat
    JSON tanasidagi "error" fieldi orqali bildiriladi.
    
    Args:
        view_func: View funksiyasi
        
    Returns:
        Decorated funksiya
    """
    @wraps(view_func)
    def wrapper(self, request: Request, *args, **kwargs):
        # IP whitelist tekshiruvi
        if not check_ip_whitelist(request):
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": PaymeError.ACCESS_DENIED,
                    "message": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en"),
                    "data": "Access denied: IP not in whitelist"
                },
                "id": None
            }
            # MUHIM: HTTP 200 bilan qaytariladi (Payme protokoli talabi)
            return JsonResponse(error_response, status=200)
        
        # Basic Auth tekshiruvi
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": PaymeError.ACCESS_DENIED,
                    "message": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en"),
                    "data": "Authorization header is missing"
                },
                "id": None
            }
            # MUHIM: HTTP 200 bilan qaytariladi (Payme protokoli talabi)
            return JsonResponse(error_response, status=200)
        
        credentials = parse_basic_auth(auth_header)
        if not credentials:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": PaymeError.ACCESS_DENIED,
                    "message": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en"),
                    "data": "Invalid authorization header format"
                },
                "id": None
            }
            # MUHIM: HTTP 200 bilan qaytariladi (Payme protokoli talabi)
            return JsonResponse(error_response, status=200)
        
        username, password = credentials
        if not verify_payme_credentials(username, password):
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": PaymeError.ACCESS_DENIED,
                    "message": PaymeError.get_error_message(PaymeError.ACCESS_DENIED, "en"),
                    "data": "Invalid credentials"
                },
                "id": None
            }
            # MUHIM: HTTP 200 bilan qaytariladi (Payme protokoli talabi)
            return JsonResponse(error_response, status=200)
        
        # Barcha tekshiruvlar muvaffaqiyatli o'tdi
        return view_func(self, request, *args, **kwargs)
    
    return wrapper
