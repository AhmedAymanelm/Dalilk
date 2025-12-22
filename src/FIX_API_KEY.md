# 🔧 إصلاح مشكلة الـ API Key

## المشكلة الحالية:
```
API key expired. Please renew the API key.
```

## الحل خطوة بخطوة:

### 1️⃣ إنشاء API Key جديد:

1. اذهب إلى: **https://ai.google.dev/**
2. سجل دخول بحساب Google
3. اضغط على **"Get API Key"** أو **"Create API Key"**
4. اختر مشروع أو أنشئ مشروع جديد
5. انسخ الـ API Key

### 2️⃣ إضافة الـ API Key في ملف .env:

**الموقع:** `/Users/ahmed/Desktop/Graduation project/Ai/.env`

**أضف أو عدل السطر:**
```
GEMINI_API_KEY=your_new_api_key_here
```

**مثال:**
```
GEMINI_API_KEY=AIzaSyD8sLxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3️⃣ إعادة تشغيل السيرفر:

```bash
cd "/Users/ahmed/Desktop/Graduation project/Ai/src"
source ../venv/bin/activate

# أوقف السيرفر القديم
lsof -ti:8000 | xargs kill -9

# شغل السيرفر تاني
python -c "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8000)" &
```

### 4️⃣ التجربة:

```bash
python voice_record.py
```

## ✅ التحقق من الـ API Key:

```bash
cd "/Users/ahmed/Desktop/Graduation project/Ai/src"
source ../venv/bin/activate
python -c "from helper.config import get_settings; print('API Key:', get_settings().GEMINI_API_KEY[:20] + '...')"
```

## ⚠️ ملاحظات مهمة:

- تأكد إن الـ API Key في ملف `.env` في المجلد الرئيسي (`Ai/.env`)
- لا تضع مسافات حول علامة `=`
- لا تضع علامات اقتباس حول الـ API Key
- تأكد إن الـ API Key مفعل في Google Cloud Console

## 🔗 روابط مفيدة:

- إنشاء API Key: https://ai.google.dev/
- التحقق من الـ Quota: https://ai.dev/usage?tab=rate-limit
- وثائق Gemini API: https://ai.google.dev/docs

