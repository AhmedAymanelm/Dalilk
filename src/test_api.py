#!/usr/bin/env python3
"""
مثال عملي لاستخدام Voice API
"""

import requests
import json
import sys

def test_voice_api():
    """اختبار الـ Voice API"""
    
    print("=" * 60)
    print("🧪 اختبار Voice API للـ Flutter")
    print("=" * 60)
    
    # تفاصيل الطلب
    url = "http://localhost:8000/api/v1/voice-whisper/voice-chat"
    
    print(f"\n📍 الـ Endpoint: {url}")
    print("\n📤 المطلوب:")
    print("   - ملف صوتي (audio)")
    print("   - session_id (اختياري)")
    print("   - limit (عدد السيارات)")
    
    # افحص إذا كان في ملف صوتي
    audio_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not audio_path:
        print("\n⚠️  لم يتم تحديد ملف صوتي")
        print("\n💡 للاستخدام:")
        print("   python test_api.py <path_to_audio_file>")
        print("\n📋 مثال:")
        print("   python test_api.py test_audio.wav")
        print("\n🎤 أو سجل صوت جديد:")
        print("   ffmpeg -f avfoundation -i ':0' -t 5 -ar 16000 -ac 1 my_audio.wav -y")
        print("   python test_api.py my_audio.wav")
        return
    
    # إرسال الطلب
    print(f"\n📤 جاري إرسال: {audio_path}")
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': f}
            data = {
                'session_id': 'flutter_test_001',
                'limit': 5
            }
            
            print("⏳ انتظر شوية...")
            response = requests.post(url, files=files, data=data, timeout=60)
        
        # معالجة النتيجة
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 60)
            print("✅ نجح الطلب!")
            print("=" * 60)
            
            # عرض النتائج
            if result.get('success'):
                transcript = result.get('transcript', '')
                response_text = result.get('response_text', '')
                cars = result.get('cars', [])
                audio_format = result.get('audio_format', '')
                
                print(f"\n📝 النص المستخرج:")
                print(f"   '{transcript}'")
                
                print(f"\n🤖 رد البوت:")
                print(f"   '{response_text}'")
                
                print(f"\n🚗 عدد السيارات: {len(cars)}")
                
                if cars:
                    print("\n🚘 السيارات المقترحة:")
                    for i, car in enumerate(cars[:3], 1):
                        print(f"   {i}. {car.get('name')} - {car.get('price')}")
                        print(f"      التقييم: {car.get('rating')} - {car.get('rating_text')}")
                
                print(f"\n🔊 صيغة الصوت: {audio_format}")
                
                has_audio = bool(result.get('audio_base64'))
                print(f"💬 الصوت موجود: {'✅ نعم' if has_audio else '❌ لا'}")
                
                # معلومات للـ Flutter
                print("\n" + "=" * 60)
                print("📱 للاستخدام في Flutter:")
                print("=" * 60)
                print("\n✅ الحقول المتاحة في Response:")
                print(f"   • transcript: {type(transcript).__name__}")
                print(f"   • response_text: {type(response_text).__name__}")
                print(f"   • cars: Array ({len(cars)} items)")
                print(f"   • audio_base64: String")
                print(f"   • audio_format: {audio_format}")
                
            else:
                print(f"\n❌ فشل: {result.get('error', 'خطأ غير معروف')}")
        
        else:
            print(f"\n❌ خطأ في الطلب: {response.status_code}")
            print(f"   {response.text[:200]}")
    
    except FileNotFoundError:
        print(f"\n❌ الملف غير موجود: {audio_path}")
    except requests.exceptions.ConnectionError:
        print("\n❌ السيرفر غير شغال!")
        print("   شغّل السيرفر الأول:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_voice_api()
