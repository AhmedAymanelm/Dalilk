# 🎤 Voice API للـ Flutter

## 📍 API Endpoint الأساسي

```
POST http://localhost:8000/api/v1/voice-whisper/voice-chat
```

**الميزات:**
- ✅ بدون quota limits (يستخدم Whisper محلياً)
- ✅ يرجع النص + الرد + السيارات + الصوت
- ✅ سريع ودقيق في التعرف على العربي

---

## 📤 Request Format

### Parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio` | File | ✅ Yes | ملف صوتي (wav, mp3, m4a, etc.) |
| `session_id` | String | ❌ No | معرف الجلسة (للحفاظ على سياق المحادثة) |
| `limit` | Integer | ❌ No | عدد السيارات المطلوبة (default: 5) |

### Example using cURL:

```bash
curl -X POST "http://localhost:8000/api/v1/voice-whisper/voice-chat" \
  -F "audio=@/path/to/audio.wav" \
  -F "session_id=user123" \
  -F "limit=5"
```

---

## 📥 Response Format

```json
{
  "success": true,
  "transcript": "عايز عربية في حدود 300 ألف جنيه",
  "response_text": "تمام، تحب استخدام شخصي ولا عيلة؟",
  "cars": [
    {
      "name": "MG 5",
      "price": "320,000 جنيه",
      "rating": "4.2",
      "id": "mg5_2024",
      "images": ["url1", "url2"],
      "specs": {
        "engine": "1.5 لتر",
        "transmission": "أوتوماتيك CVT",
        "fuel_type": "بنزين"
      },
      "rating_text": "تقييم جيد جداً",
      "score": 0.95
    }
  ],
  "audio_base64": "base64_encoded_audio_string",
  "audio_format": "mp3"
}
```

---

## 🔧 Flutter Implementation Example

### 1. إضافة Dependencies

في `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  path_provider: ^2.1.1
  audioplayers: ^5.2.1
  record: ^5.0.4
```

### 2. دالة إرسال الصوت

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class VoiceApiService {
  final String baseUrl = 'http://localhost:8000'; // غيرها لـ IP السيرفر
  
  Future<Map<String, dynamic>> sendVoiceMessage({
    required File audioFile,
    String? sessionId,
    int limit = 5,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/voice-whisper/voice-chat');
      
      var request = http.MultipartRequest('POST', uri);
      
      // إضافة ملف الصوت
      request.files.add(
        await http.MultipartFile.fromPath(
          'audio',
          audioFile.path,
        ),
      );
      
      // إضافة المعاملات الأخرى
      if (sessionId != null) {
        request.fields['session_id'] = sessionId;
      }
      request.fields['limit'] = limit.toString();
      
      // إرسال الطلب
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
}
```

### 3. استخدام الدالة

```dart
// مثال على الاستخدام
void _sendVoice() async {
  final voiceService = VoiceApiService();
  
  try {
    // افترض أن audioFile هو ملف الصوت المسجل
    final result = await voiceService.sendVoiceMessage(
      audioFile: recordedFile,
      sessionId: 'user_123',
      limit: 5,
    );
    
    // استخراج البيانات
    String transcript = result['transcript'];
    String responseText = result['response_text'];
    List cars = result['cars'] ?? [];
    String audioBase64 = result['audio_base64'];
    
    // عرض النص
    print('ما قلته: $transcript');
    print('رد البوت: $responseText');
    print('عدد السيارات: ${cars.length}');
    
    // تشغيل الصوت (اختياري)
    if (audioBase64.isNotEmpty) {
      await _playAudioFromBase64(audioBase64);
    }
    
  } catch (e) {
    print('خطأ: $e');
  }
}
```

### 4. تشغيل الصوت من Base64

```dart
import 'dart:typed_data';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';

Future<void> _playAudioFromBase64(String base64Audio) async {
  try {
    // تحويل base64 إلى bytes
    Uint8List bytes = base64Decode(base64Audio);
    
    // حفظ في ملف مؤقت
    final tempDir = await getTemporaryDirectory();
    final tempFile = File('${tempDir.path}/response_audio.mp3');
    await tempFile.writeAsBytes(bytes);
    
    // تشغيل الصوت
    final player = AudioPlayer();
    await player.play(DeviceFileSource(tempFile.path));
  } catch (e) {
    print('خطأ في تشغيل الصوت: $e');
  }
}
```

---

## 🧪 اختبار الـ API

### من Terminal:

```bash
# تسجيل صوت بسيط (5 ثواني)
ffmpeg -f avfoundation -i ":0" -t 5 -ar 16000 -ac 1 test_audio.wav -y

# إرسال للـ API
curl -X POST "http://localhost:8000/api/v1/voice-whisper/voice-chat" \
  -F "audio=@test_audio.wav" \
  -F "session_id=test123" \
  -F "limit=5"
```

### من Python Script:

```python
import requests

url = "http://localhost:8000/api/v1/voice-whisper/voice-chat"

with open("test_audio.wav", "rb") as f:
    files = {"audio": f}
    data = {
        "session_id": "test123",
        "limit": 5
    }
    response = requests.post(url, files=files, data=data)
    
result = response.json()
print(f"النص: {result['transcript']}")
print(f"الرد: {result['response_text']}")
print(f"السيارات: {len(result.get('cars', []))}")
```

---

## 🌐 ملاحظات مهمة للـ Flutter

### 1. استخدام IP الصحيح

```dart
// للتطوير المحلي على Android Emulator
final String baseUrl = 'http://10.0.2.2:8000';

// للتطوير على جهاز حقيقي
final String baseUrl = 'http://192.168.1.100:8000'; // IP الجهاز

// للـ Production
final String baseUrl = 'https://your-domain.com';
```

### 2. Permissions في Android

في `AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
```

### 3. Permissions في iOS

في `Info.plist`:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>نحتاج إذن الميكروفون للتسجيل الصوتي</string>
```

---

## 📊 Response Fields Details

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | نجاح العملية |
| `transcript` | String | النص المستخرج من الصوت |
| `response_text` | String | رد الذكاء الاصطناعي (نصي) |
| `cars` | Array | قائمة السيارات المقترحة |
| `audio_base64` | String | الرد الصوتي بصيغة base64 |
| `audio_format` | String | صيغة الصوت (mp3) |

### Car Object Structure:

```dart
class Car {
  final String name;
  final String price;
  final String rating;
  final String id;
  final List<String> images;
  final Map<String, dynamic> specs;
  final String ratingText;
  final double? score;
  
  Car.fromJson(Map<String, dynamic> json)
      : name = json['name'] ?? '',
        price = json['price'] ?? '',
        rating = json['rating'] ?? '',
        id = json['id'] ?? '',
        images = List<String>.from(json['images'] ?? []),
        specs = json['specs'] ?? {},
        ratingText = json['rating_text'] ?? '',
        score = json['score']?.toDouble();
}
```

---

## 🔗 Endpoints الأخرى المتاحة

### 1. Speech-to-Text فقط
```
POST /api/v1/voice-whisper/speech-to-text
```

### 2. Text-to-Speech فقط
```
POST /api/v1/voice/text-to-speech?text=مرحبا
```

### 3. البحث النصي (بدون صوت)
```
POST /api/v1/nlp/rag_search
```

---

## 📝 مثال كامل للاستخدام

```bash
# 1. تشغيل السيرفر
cd "/Users/ahmed/Desktop/Graduation project/Ai/src"
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. اختبار من terminal آخر
curl -X POST "http://localhost:8000/api/v1/voice-whisper/voice-chat" \
  -F "audio=@test_audio.wav" \
  -F "session_id=flutter_user_123" \
  -F "limit=5" \
  | jq '.'
```

---

**تاريخ آخر تحديث:** 2025-12-21  
**الحالة:** ✅ جاهز للاستخدام
