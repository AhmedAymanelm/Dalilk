# 🎤 دليل اختبار Voice Endpoints

السيرفر شغال على: **http://localhost:8000**

## 📋 Endpoints المتاحة:

### 1. تحويل الصوت إلى نص
```bash
curl -X POST "http://localhost:8000/api/v1/voice/speech-to-text" \
  -F "audio=@/path/to/your/audio.wav"
```

### 2. تحويل النص إلى صوت
```bash
curl -X POST "http://localhost:8000/api/v1/voice/text-to-speech?text=مرحبا%20هذا%20اختبار" \
  --output response.mp3
```

### 3. محادثة صوتية كاملة (مربوطة مع RAG) ⭐
```bash
curl -X POST "http://localhost:8000/api/v1/voice/voice-chat" \
  -F "audio=@/path/to/your/audio.wav" \
  -F "session_id=user123" \
  -F "limit=5"
```

### 4. محادثة صوتية مع stream مباشر
```bash
curl -X POST "http://localhost:8000/api/v1/voice/voice-chat-stream" \
  -F "audio=@/path/to/your/audio.wav" \
  -F "session_id=user123" \
  --output response.mp3
```

## 🧪 استخدام ملف الاختبار:

```bash
cd "/Users/ahmed/Desktop/Graduation project/Ai/src"
source ../venv/bin/activate
python test_voice.py
```

**ملاحظة:** غير `audio_file` في `test_voice.py` بمسار ملف صوتي عندك.

## 🌐 استخدام Swagger UI:

افتح المتصفح وروح على:
**http://localhost:8000/docs**

هتلاقي كل الـ endpoints مع إمكانية التجربة مباشرة من المتصفح!

## 📝 مثال بسيط:

```python
import requests

# اختبار voice-chat
url = "http://localhost:8000/api/v1/voice/voice-chat"
with open("test_audio.wav", "rb") as f:
    files = {"audio": f}
    data = {"session_id": "test", "limit": 5}
    response = requests.post(url, files=files, data=data)
    
result = response.json()
print(f"النص: {result['transcript']}")
print(f"الرد: {result['response_text']}")
```

## ⚠️ متطلبات:

- تأكد إن `GEMINI_API_KEY` موجود في `.env`
- تأكد إن `ELEVENLABS_API_KEY` موجود في `.env`
- ملف الصوت لازم يكون بصيغة مدعومة (wav, mp3, m4a, etc.)

