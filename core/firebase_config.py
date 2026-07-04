"""
Firebase Admin SDK konfiguratsiyasi.
Firestore database bilan bog'lanish uchun ishlatiladi.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

# Firebase service account fayl yo'li
cred_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "secrets", 
    "firebase-service-account.json"
)

# Firebase credentials'ni yuklash
cred = credentials.Certificate(cred_path)

# Firebase Admin SDK'ni initialize qilish (faqat bir marta)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore client'ini yaratish
db = firestore.client()
