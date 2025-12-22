"""
ملف اختبار بسيط لـ voice endpoints
استخدم هذا الملف لاختبار الـ voice chat
"""

import requests
import json

# عنوان السيرفر
BASE_URL = "http://localhost:8000"

def test_speech_to_text(audio_file_path):
    """اختبار تحويل الصوت إلى نص"""
    print("🧪 اختبار تحويل الصوت إلى نص...")
    
    url = f"{BASE_URL}/api/v1/voice/speech-to-text"
    
    with open(audio_file_path, 'rb') as f:
        files = {'audio': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ النص المستخرج: {result.get('transcript')}")
        return result.get('transcript')
    else:
        print(f"❌ خطأ: {response.status_code}")
        print(response.text)
        return None

def test_text_to_speech(text):
    """اختبار تحويل النص إلى صوت"""
    print(f"\n🧪 اختبار تحويل النص إلى صوت...")
    
    url = f"{BASE_URL}/api/v1/voice/text-to-speech"
    params = {'text': text}
    
    response = requests.post(url, params=params)
    
    if response.status_code == 200:
        # حفظ الملف الصوتي
        output_file = "test_output.mp3"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"✅ تم حفظ الصوت في: {output_file}")
        return output_file
    else:
        print(f"❌ خطأ: {response.status_code}")
        print(response.text)
        return None

def test_voice_chat(audio_file_path, session_id="test_session"):
    """اختبار المحادثة الصوتية الكاملة"""
    print(f"\n🧪 اختبار المحادثة الصوتية الكاملة...")
    
    url = f"{BASE_URL}/api/v1/voice/voice-chat"
    
    with open(audio_file_path, 'rb') as f:
        files = {'audio': f}
        data = {
            'session_id': session_id,
            'limit': 5
        }
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ النص المستخرج: {result.get('transcript')}")
        print(f"✅ رد البوت: {result.get('response_text')}")
        
        # حفظ الصوت
        if result.get('audio_base64'):
            import base64
            audio_data = base64.b64decode(result['audio_base64'])
            output_file = "voice_chat_response.mp3"
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            print(f"✅ تم حفظ الصوت في: {output_file}")
        
        # عرض السيارات إذا وجدت
        cars = result.get('cars', [])
        if cars:
            print(f"\n🚗 السيارات المقترحة ({len(cars)}):")
            for car in cars[:3]:  # أول 3 سيارات
                print(f"  - {car.get('name')} - {car.get('price')}")
        
        return result
    else:
        print(f"❌ خطأ: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("اختبار Voice Endpoints")
    print("=" * 50)
    
    # استبدل هذا بمسار ملف الصوت الخاص بك
    audio_file = "../test_silent.wav"  # أو أي ملف صوتي آخر
    
    import os
    if not os.path.exists(audio_file):
        print(f"\n⚠️  ملف الصوت غير موجود: {audio_file}")
        print("الرجاء تحديث audio_file في الكود بمسار ملف صوتي صحيح")
        print("\nيمكنك استخدام:")
        print("1. test_speech_to_text('path/to/audio.wav')")
        print("2. test_text_to_speech('مرحبا، عايز عربية في حدود 200 ألف')")
        print("3. test_voice_chat('path/to/audio.wav')")
    else:
        # اختبار كامل
        transcript = test_speech_to_text(audio_file)
        
        if transcript:
            # اختبار تحويل النص إلى صوت
            test_text_to_speech("هذا اختبار لتحويل النص إلى صوت")
            
            # اختبار المحادثة الكاملة
            test_voice_chat(audio_file)

