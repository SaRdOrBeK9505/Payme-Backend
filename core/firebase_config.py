"""
Firebase Admin SDK konfiguratsiyasi.
Firestore database bilan bog'lanish uchun ishlatiladi.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Firebase service account fayl yo'li
cred_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "secrets", 
    "firebase-service-account.json"
)

# Firebase service account faylini tekshirish
if not os.path.exists(cred_path):
    error_message = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    FIREBASE CONFIGURATION ERROR                          ║
╚══════════════════════════════════════════════════════════════════════════╝

❌ Firebase service account JSON fayli topilmadi!

📁 Kutilayotgan fayl yo'li:
   {cred_path}

🔧 Tuzatish uchun quyidagi qadamlarni bajaring:

1️⃣  Firebase Console'ga kiring:
   https://console.firebase.google.com/

2️⃣  Project Settings → Service Accounts → Generate new private key

3️⃣  Yuklab olingan JSON faylni quyidagi papkaga joylashtiring:
   {os.path.dirname(cred_path)}/

4️⃣  Fayl nomini o'zgartiring:
   firebase-service-account.json

5️⃣  Fayl ruxsatlarini tekshiring (read access bo'lishi kerak)

📖 Batafsil yo'riqnoma: SETUP_GUIDE.md faylida

════════════════════════════════════════════════════════════════════════════
"""
    print(error_message, file=sys.stderr)
    raise FileNotFoundError(
        f"Firebase service account file not found at: {cred_path}\n"
        f"Please download the file from Firebase Console and place it in the 'secrets/' directory.\n"
        f"See SETUP_GUIDE.md for detailed instructions."
    )

# Firebase credentials'ni yuklash
try:
    cred = credentials.Certificate(cred_path)
except Exception as e:
    error_message = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║              FIREBASE CREDENTIALS LOADING ERROR                          ║
╚══════════════════════════════════════════════════════════════════════════╝

❌ Firebase service account fayli noto'g'ri formatda yoki buzilgan!

📁 Fayl yo'li: {cred_path}

🔍 Xato: {str(e)}

🔧 Tuzatish uchun:

1️⃣  Fayl to'g'ri JSON formatida ekanligini tekshiring
2️⃣  Firebase Console'dan yangi fayl yuklab oling
3️⃣  Faylni qayta joylashtiring

════════════════════════════════════════════════════════════════════════════
"""
    print(error_message, file=sys.stderr)
    raise

# Firebase Admin SDK'ni initialize qilish (faqat bir marta)
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app(cred)
    except Exception as e:
        error_message = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║              FIREBASE INITIALIZATION ERROR                               ║
╚══════════════════════════════════════════════════════════════════════════╝

❌ Firebase Admin SDK initialize qilishda xato!

🔍 Xato: {str(e)}

🔧 Mumkin bo'lgan sabablar:

1️⃣  Internet aloqasi yo'q
2️⃣  Service account ruxsatlari noto'g'ri
3️⃣  Firebase API o'chirilgan
4️⃣  Project ID noto'g'ri

════════════════════════════════════════════════════════════════════════════
"""
        print(error_message, file=sys.stderr)
        raise

# Firestore client'ini yaratish
try:
    db = firestore.client()
except Exception as e:
    error_message = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                 FIRESTORE CLIENT ERROR                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

❌ Firestore client yaratishda xato!

🔍 Xato: {str(e)}

🔧 Mumkin bo'lgan sabablar:

1️⃣  Firestore API o'chirilgan (Firebase Console'da yoqing)
2️⃣  Service account Firestore ruxsatiga ega emas
3️⃣  Network aloqasi yo'q

════════════════════════════════════════════════════════════════════════════
"""
    print(error_message, file=sys.stderr)
    raise
