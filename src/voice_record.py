#!/usr/bin/env python3
"""
سكريبت Python لتسجيل الصوت وإرساله للـ API وحفظ الرد
"""

import requests
import base64
import json
import sys
import os
from datetime import datetime
import subprocess

# استخدام Whisper endpoint (بدون quota limits)
API_URL = "http://localhost:8000/api/v1/voice-whisper/voice-chat"

def record_audio(output_file, duration=None):
    """تسجيل الصوت - تفاعلي (يبدأ وينتهي عند الضغط على Enter)"""
    print("🎤 جاري تسجيل الصوت...")
    print("📝 اضغط Enter للبدء، ثم اضغط Enter مرة أخرى للإنهاء")
    print("   (أو اضغط Ctrl+C للإيقاف)\n")
    
    # انتظار الضغط على Enter للبدء
    try:
        input("⏸️  اضغط Enter للبدء في التسجيل...")
    except (EOFError, KeyboardInterrupt):
        print("\n⚠️  لا يمكن استخدام input() في هذا الـ terminal")
        print("🔄 استخدام وضع تلقائي (10 ثواني)...")
        duration = 10
        print(f"🔴 جاري التسجيل لمدة {duration} ثانية...\n")
    
    try:
        # استخدام ffmpeg مع تسجيل تفاعلي
        try:
            # إنشاء عملية تسجيل في الخلفية
            process = subprocess.Popen(
                ["ffmpeg", "-f", "avfoundation", "-i", ":0", 
                 "-ar", "16000", "-ac", "1", 
                 output_file, "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # انتظار الضغط على Enter للإنهاء
            try:
                input()  # انتظار Enter
                print("\n⏹️  جاري إنهاء التسجيل...")
                process.terminate()
                process.wait(timeout=2)
                return True
            except KeyboardInterrupt:
                print("\n⏹️  تم إيقاف التسجيل")
                process.terminate()
                process.wait(timeout=2)
                return os.path.exists(output_file) and os.path.getsize(output_file) > 0
                
        except FileNotFoundError:
            pass
        
        # استخدام sox/rec كبديل
        try:
            print("⚠️  استخدام sox (اضغط Ctrl+C للإنهاء)")
            subprocess.run(
                ["rec", "-r", "16000", "-c", "1", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, KeyboardInterrupt):
            pass
        
        # استخدام arecord (Linux)
        try:
            print("⚠️  استخدام arecord (اضغط Ctrl+C للإنهاء)")
            subprocess.run(
                ["arecord", "-f", "cd", "-t", "wav", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, KeyboardInterrupt):
            pass
        
        print("❌ لم يتم العثور على أداة تسجيل صوتي")
        print("\nالرجاء تثبيت أحد الأدوات التالية:")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install alsa-utils")
        return False
        
    except Exception as e:
        print(f"❌ خطأ في التسجيل: {str(e)}")
        return False

def send_audio_to_api(audio_file, session_id="default_session"):
    """إرسال الصوت للـ API مع retry تلقائي"""
    print(f"\n📤 جاري إرسال الصوت للـ API...")
    
    import time
    import re
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(audio_file, 'rb') as f:
                files = {'audio': f}
                data = {
                    'session_id': session_id,
                    'limit': 5
                }
                response = requests.post(API_URL, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429 or response.status_code == 500:
                # محاولة استخراج وقت الانتظار من الرسالة
                error_text = response.text
                wait_time = 60  # افتراضي
                
                wait_match = re.search(r'retry in ([\d.]+)s', error_text, re.IGNORECASE)
                if wait_match:
                    wait_time = int(float(wait_match.group(1))) + 2
                
                if attempt < max_retries - 1:
                    print(f"⏳ Quota منتهي، انتظار {wait_time} ثانية... (محاولة {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ خطأ في الطلب: {response.status_code}")
                    print(error_text[:500])
                    return None
            else:
                print(f"❌ خطأ في الطلب: {response.status_code}")
                print(response.text[:500])
                return None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⏳ Timeout، إعادة المحاولة... (محاولة {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            else:
                print(f"❌ Timeout بعد {max_retries} محاولات")
                return None
        except Exception as e:
            print(f"❌ خطأ في الإرسال: {str(e)}")
            return None
    
    return None

def save_audio_response(audio_base64, output_file):
    """حفظ الصوت من base64"""
    try:
        audio_data = base64.b64decode(audio_base64)
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        return True
    except Exception as e:
        print(f"⚠️  خطأ في حفظ الصوت: {str(e)}")
        return False

def play_audio(audio_file):
    """تشغيل الصوت"""
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["afplay", audio_file], check=True)
        elif sys.platform.startswith("linux"):  # Linux
            subprocess.run(["aplay", audio_file], check=True)
        else:
            print(f"💡 يمكنك تشغيل الصوت يدوياً: {audio_file}")
    except:
        print(f"💡 يمكنك تشغيل الصوت يدوياً: {audio_file}")

def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else "default_session"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_audio = f"temp_record_{timestamp}.wav"
    output_audio = f"voice_response_{timestamp}.mp3"
    
    print("=" * 50)
    print("🎤 Voice Chat - تسجيل صوتي تفاعلي")
    print("=" * 50)
    print(f"📝 Session ID: {session_id}")
    print("=" * 50)
    print()
    
    # تسجيل الصوت (تفاعلي)
    if not record_audio(temp_audio):
        print("❌ فشل تسجيل الصوت")
        return
    
    if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) == 0:
        print("❌ فشل تسجيل الصوت")
        return
    
    print("✅ تم تسجيل الصوت")
    
    # إرسال للـ API
    result = send_audio_to_api(temp_audio, session_id)
    
    if not result:
        os.remove(temp_audio)
        return
    
    if result.get('success'):
        print("\n" + "=" * 50)
        print("✅ تم استلام الرد")
        print("=" * 50)
        
        # عرض النص
        transcript = result.get('transcript', '')
        if transcript:
            print(f"\n📝 النص المستخرج:")
            print(f"   {transcript}")
        
        # عرض الرد
        response_text = result.get('response_text', '')
        if response_text:
            print(f"\n🤖 رد البوت:")
            print(f"   {response_text}")
        
        # حفظ الصوت
        audio_b64 = result.get('audio_base64', '')
        if audio_b64:
            if save_audio_response(audio_b64, output_audio):
                print(f"\n💾 تم حفظ الصوت في: {output_audio}")
                
                # عرض السيارات إذا وجدت
                cars = result.get('cars', [])
                if cars:
                    print(f"\n🚗 السيارات المقترحة ({len(cars)}):")
                    for car in cars[:3]:
                        name = car.get('name', 'غير معروف')
                        price = car.get('price', 'غير معروف')
                        print(f"   - {name}: {price}")
                
                # سؤال المستخدم إذا كان يريد تشغيل الصوت
                try:
                    play = input("\n🔊 هل تريد تشغيل الصوت الآن؟ (y/n): ").lower()
                    if play == 'y':
                        play_audio(output_audio)
                except:
                    pass
    
    # حذف الملف المؤقت
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        print(f"\n🧹 تم حذف الملف المؤقت")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  تم الإلغاء")
        sys.exit(0)

