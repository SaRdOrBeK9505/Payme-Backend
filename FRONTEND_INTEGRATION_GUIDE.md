# 🎨 Frontend Integration Guide - Payme Backend

## 📋 Umumiy Ma'lumot

Bu guide frontend (React, Next.js, Vue.js, yoki boshqa) dan Payme Backend API bilan qanday integratsiya qilish haqida.

---

## ✅ **CORS Allaqachon Sozlangan!**

Backend'da CORS configuration tayyor:

```python
# Development: Barcha originlarga ruxsat
CORS_ALLOW_ALL_ORIGINS = True

# Production: Faqat belgilangan domainlar
CORS_ALLOWED_ORIGINS = [
  'https://yourfrontend.com',
  'https://app.yourfrontend.com'
]
```

---

## 🔗 **API Endpoints**

### **Base URL**
```
Development: http://localhost:8000
Production:  https://your-backend-domain.com
```

### **1. To'lov Havolasini Yaratish**

**Endpoint:**
```
POST /api/payments/create-link/
```

**Request:**
```json
{
  "order_id": "ORD-95612789"
}
```

**Response (Success):**
```json
{
  "success": true,
  "checkout_url": "https://checkout.test.paycom.uz/eyJt...",
  "order_id": "ORD-95612789",
  "amount": 172000,
  "amount_tiyin": 17200000
}
```

**Response (Error - Order Not Found):**
```json
{
  "success": false,
  "error": "Order not found"
}
```

**Response (Error - Already Paid):**
```json
{
  "success": false,
  "error": "Order already paid"
}
```

---

## 💻 **Frontend Code Examples**

### **React / Next.js Example**

```javascript
// services/payme.js
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function createPaymentLink(orderId) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/payments/create-link/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        order_id: orderId
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to create payment link');
    }

    return data;
  } catch (error) {
    console.error('Payment link creation error:', error);
    throw error;
  }
}
```

**Component Example:**
```jsx
// components/PaymentButton.jsx
import { useState } from 'react';
import { createPaymentLink } from '@/services/payme';

export default function PaymentButton({ orderId }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePayment = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await createPaymentLink(orderId);
      
      // Payme checkout sahifasiga yo'naltirish
      window.location.href = result.checkout_url;
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={handlePayment}
        disabled={loading}
        className="bg-blue-500 text-white px-6 py-3 rounded-lg"
      >
        {loading ? 'Yuklanmoqda...' : 'Payme orqali to\'lash'}
      </button>
      
      {error && (
        <div className="text-red-500 mt-2">
          Xato: {error}
        </div>
      )}
    </div>
  );
}
```

---

### **Vue.js Example**

```javascript
// services/payme.js
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const paymeService = {
  async createPaymentLink(orderId) {
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/payments/create-link/`,
        { order_id: orderId },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to create payment link');
    }
  }
};
```

**Component Example:**
```vue
<!-- components/PaymentButton.vue -->
<template>
  <div>
    <button 
      @click="handlePayment"
      :disabled="loading"
      class="bg-blue-500 text-white px-6 py-3 rounded-lg"
    >
      {{ loading ? 'Yuklanmoqda...' : 'Payme orqali to\'lash' }}
    </button>
    
    <div v-if="error" class="text-red-500 mt-2">
      Xato: {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { paymeService } from '@/services/payme';

const props = defineProps({
  orderId: {
    type: String,
    required: true
  }
});

const loading = ref(false);
const error = ref(null);

const handlePayment = async () => {
  loading.value = true;
  error.value = null;

  try {
    const result = await paymeService.createPaymentLink(props.orderId);
    window.location.href = result.checkout_url;
  } catch (err) {
    error.value = err.message;
    loading.value = false;
  }
};
</script>
```

---

### **Vanilla JavaScript Example**

```javascript
// payme.js
async function createPayment(orderId) {
  const BACKEND_URL = 'http://localhost:8000';
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/payments/create-link/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        order_id: orderId
      })
    });

    const data = await response.json();

    if (data.success) {
      // Redirect to Payme
      window.location.href = data.checkout_url;
    } else {
      alert('Xato: ' + data.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Xato yuz berdi');
  }
}

// Usage
document.getElementById('payButton').addEventListener('click', () => {
  const orderId = 'ORD-95612789';
  createPayment(orderId);
});
```

---

## 🔄 **To'lov Jarayoni Workflow**

```
1. [Frontend] User "To'lash" tugmasini bosadi
   ↓
2. [Frontend] Backend'ga order_id yuboradi
   POST /api/payments/create-link/
   ↓
3. [Backend] Order'ni Firestore'dan tekshiradi
   - Status: pending/processing ✅
   - Status: paid/cancelled ❌
   ↓
4. [Backend] Payme checkout URL yaratadi
   ↓
5. [Frontend] User'ni Payme sahifasiga yo'naltiradi
   window.location.href = checkout_url
   ↓
6. [User] Payme'da to'lovni amalga oshiradi
   ↓
7. [Payme] Backend webhook'ga so'rov yuboradi
   POST /api/payments/webhook/
   ↓
8. [Backend] Firestore'da order statusini yangilaydi
   pending → processing → paid
   ↓
9. [Payme] User'ni return_url'ga qaytaradi
   ↓
10. [Frontend] Order statusini tekshiradi va success page ko'rsatadi
```

---

## 📊 **Firestore Order Strukturasi**

### **Order Document (orders collection)**

```json
{
  "id": "ORD-95612789",
  "userId": "user_123",
  "status": "pending",  // pending, processing, paid, delivered, cancelled
  "total": 172000,      // so'mda (MUHIM!)
  "items": [
    {
      "productId": "prod_001",
      "name": "Mahsulot nomi",
      "quantity": 2,
      "price": 86000
    }
  ],
  "createdAt": "2026-07-04T10:00:00Z",
  "updatedAt": "2026-07-04T10:00:00Z",
  "paidAt": null,
  "paymeTransactionId": null
}
```

**MUHIM:** 
- `total` maydon **so'mda** (masalan: 172000)
- Backend avtomatik **tiyinga** o'zgartiradi (* 100)
- Payme **faqat tiyin** bilan ishlaydi (masalan: 17200000)

---

## 🎯 **Frontend Development Setup**

### **1. Environment Variables**

**Next.js (.env.local):**
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Vue.js / Vite (.env):**
```env
VITE_BACKEND_URL=http://localhost:8000
```

**React (CRA) (.env):**
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

### **2. Backend Server Ishga Tushirish**

```bash
cd payme_backend
python manage.py runserver 8000
```

### **3. Frontend Server Ishga Tushirish**

```bash
# Next.js
npm run dev

# Vue.js / Vite
npm run dev

# React (CRA)
npm start
```

---

## 🧪 **Testing**

### **1. Test Order Yaratish (Firestore)**

```javascript
// Firebase Admin SDK (Backend script)
const admin = require('firebase-admin');
const db = admin.firestore();

async function createTestOrder() {
  const orderRef = db.collection('orders').doc('ORD-TEST-001');
  
  await orderRef.set({
    id: 'ORD-TEST-001',
    userId: 'test_user',
    status: 'pending',
    total: 50000,  // 50,000 so'm
    items: [
      {
        productId: 'prod_001',
        name: 'Test Product',
        quantity: 1,
        price: 50000
      }
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  });
  
  console.log('✅ Test order created: ORD-TEST-001');
}

createTestOrder();
```

### **2. Frontend'da Test Qilish**

```javascript
// Browser Console'da
async function testPayment() {
  const response = await fetch('http://localhost:8000/api/payments/create-link/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id: 'ORD-TEST-001' })
  });
  
  const data = await response.json();
  console.log(data);
  
  if (data.success) {
    window.open(data.checkout_url, '_blank');
  }
}

testPayment();
```

### **3. Test Karta (Payme Test Environment)**

```
Card Number: 8600 0000 0000 0000
Expiry: 03/99
CVV: 666
SMS Code: 666666
```

---

## 🚀 **Production Deployment**

### **1. Backend (.env - Production)**

```env
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

PAYME_MERCHANT_ID=your_production_merchant_id
PAYME_KEY=your_production_key
PAYME_ALLOWED_IPS=185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
```

### **2. Frontend (.env - Production)**

```env
NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com
```

### **3. Payme Cabinet Configuration**

```
Webhook URL: https://api.yourdomain.com/api/payments/webhook/
Return URL: https://yourdomain.com/payment/success
```

---

## ❓ **FAQ**

### **Q: CORS xatosi chiqsa?**
**A:** Backend'da `CORS_ALLOWED_ORIGINS` ga frontend URL'ingizni qo'shing.

### **Q: Order status qachon yangilanadi?**
**A:** Payme webhook'dan keyin (avtomatik). Frontend'da Firebase realtime listener qo'yishingiz mumkin.

### **Q: Test kartasi ishlamasa?**
**A:** Payme Test Merchant ID va KEY to'g'ri ekanligini tekshiring.

### **Q: Webhook localhost'da qanday test qilaman?**
**A:** ngrok yoki localtunnel ishlatib public URL oching.

---

## 📚 **Qo'shimcha Resurslar**

- [Payme Developer Docs](https://developer.help.paycom.uz/)
- [Firebase Firestore Docs](https://firebase.google.com/docs/firestore)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)

---

## 🎉 **Tayyor!**

Endi frontend'dan backend'ni ishlatishingiz mumkin!

**Next Steps:**
1. ✅ Backend serverni ishga tushiring
2. ✅ Frontend'da API service yarating
3. ✅ Payment button component qo'shing
4. ✅ Test qiling
5. ✅ Production'ga deploy qiling

---

*Last Updated: 2026-07-04*
*Version: 1.0.0*
