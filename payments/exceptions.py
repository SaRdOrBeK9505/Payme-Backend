"""
Payme Merchant API uchun maxsus exception'lar.
"""

from .constants import PaymeError


class PaymeException(Exception):
    """
    Payme Merchant API uchun maxsus exception.
    
    Bu exception Payme API xatolarini boshqarish uchun ishlatiladi.
    Har bir exception xato kodi va xabarini o'z ichiga oladi.
    """
    
    def __init__(self, code: int, message: str, data: dict = None):
        """
        PaymeException yaratadi.
        
        Args:
            code: Payme xato kodi (PaymeError.* konstantalaridan)
            message: Xato xabari
            data: Qo'shimcha ma'lumotlar (ixtiyoriy)
        """
        self.code = code
        self.message = message
        self.data = data or {}
        
        # Parent class'ni chaqirish
        super().__init__(f"[{code}] {message}")
    
    def to_dict(self) -> dict:
        """
        Exception'ni dictionary formatiga o'tkazadi.
        
        Returns:
            Xato ma'lumotlarini o'z ichiga olgan dictionary
        """
        return {
            "code": self.code,
            "message": PaymeError.get_error_message(self.code, "en"),
            "data": self.message
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"PaymeException(code={self.code}, message={self.message})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"PaymeException(code={self.code}, message='{self.message}', data={self.data})"
