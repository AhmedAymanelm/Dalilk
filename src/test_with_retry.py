#!/usr/bin/env python3
"""
اختبار سريع مع retry للـ API
"""

import requests
import time
import sys

API_URL = "http://localhost:8000/api/v1/voice/voice-chat"

def test_with_retry(audio_file, max_retries=3):
    """اختبار مع retry"""
    for attempt in range(max_retries):
        try:
            print(f"\n🔄 المحاولة {attempt + 1}/{max_retries}...")
            
            with open(audio_file, 'rb') as f:
                files = {'audio': f}
                data = {'session_id': 'test', 'limit': 5}
                response = requests.post(API_URL, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ نجح!")
                    print(f"📝 النص: {result.get('transcript', '')}")
                    print(f"🤖 الرد: {result.get('response_text', '')[:100]}...")
                    return result
                else:
                    print(f"❌ فشل: {result.get('error', 'Unknown error')}")
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 10
                print(f"⏳ Quota exceeded. انتظار {wait_time} ثانية...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
            else:
                print(f"❌ خطأ {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ خطأ: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    return None

if __name__ == "__main__":
    # البحث عن ملف صوتي
    import os
    import glob
    
    audio_files = glob.glob("temp_record_*.wav") + glob.glob("temp_voice_*.wav")
    
    if not audio_files:
        print("❌ لم يتم العثور على ملف صوتي")
        print("الرجاء تسجيل صوت أولاً باستخدام: python voice_record.py")
        sys.exit(1)
    
    audio_file = sorted(audio_files)[-1]  # أحدث ملف
    print(f"📁 استخدام الملف: {audio_file}")
    
    result = test_with_retry(audio_file)
    
    if result and result.get('audio_base64'):
        import base64
        audio_data = base64.b64decode(result['audio_base64'])
        output_file = "test_response.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        print(f"\n💾 تم حفظ الرد في: {output_file}")

