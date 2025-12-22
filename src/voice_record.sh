#!/bin/bash

# سكريبت لتسجيل الصوت وإرساله للـ API وحفظ الرد

API_URL="http://localhost:8000/api/v1/voice/voice-chat"
SESSION_ID="${1:-default_session}"
OUTPUT_FILE="voice_response_$(date +%Y%m%d_%H%M%S).mp3"
TEMP_AUDIO="temp_record_$(date +%Y%m%d_%H%M%S).wav"

echo "🎤 تسجيل الصوت..."
echo "اضغط Enter للبدء، ثم اضغط Ctrl+C للتوقف عن التسجيل"
read

# محاولة تسجيل الصوت باستخدام أدوات مختلفة
if command -v rec &> /dev/null; then
    # استخدام sox/rec
    rec -r 16000 -c 1 "$TEMP_AUDIO" trim 0 30
elif command -v ffmpeg &> /dev/null; then
    # استخدام ffmpeg
    echo "🎙️  جاري التسجيل (30 ثانية)..."
    ffmpeg -f avfoundation -i ":0" -ar 16000 -ac 1 -t 30 "$TEMP_AUDIO" -y 2>/dev/null
elif command -v arecord &> /dev/null; then
    # استخدام arecord (Linux)
    arecord -f cd -t wav -d 30 "$TEMP_AUDIO"
else
    echo "❌ لم يتم العثور على أداة تسجيل صوتي"
    echo "الرجاء تثبيت أحد الأدوات التالية:"
    echo "  - sox (macOS: brew install sox)"
    echo "  - ffmpeg (macOS: brew install ffmpeg)"
    echo "  - arecord (Linux: sudo apt-get install alsa-utils)"
    exit 1
fi

if [ ! -f "$TEMP_AUDIO" ] || [ ! -s "$TEMP_AUDIO" ]; then
    echo "❌ فشل تسجيل الصوت"
    exit 1
fi

echo "✅ تم تسجيل الصوت"
echo "📤 جاري إرسال الصوت للـ API..."

# إرسال الصوت للـ API
RESPONSE=$(curl -s -X POST "$API_URL" \
    -F "audio=@$TEMP_AUDIO" \
    -F "session_id=$SESSION_ID" \
    -F "limit=5")

# التحقق من نجاح الطلب
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ تم استلام الرد"
    
    # استخراج النص والرد
    TRANSCRIPT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('transcript', ''))" 2>/dev/null)
    RESPONSE_TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response_text', ''))" 2>/dev/null)
    AUDIO_B64=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('audio_base64', ''))" 2>/dev/null)
    
    if [ ! -z "$TRANSCRIPT" ]; then
        echo ""
        echo "📝 النص المستخرج:"
        echo "$TRANSCRIPT"
        echo ""
    fi
    
    if [ ! -z "$RESPONSE_TEXT" ]; then
        echo "🤖 رد البوت:"
        echo "$RESPONSE_TEXT"
        echo ""
    fi
    
    # حفظ الصوت
    if [ ! -z "$AUDIO_B64" ]; then
        echo "$AUDIO_B64" | python3 -c "import sys, base64; base64.b64decode(sys.stdin.read())" > "$OUTPUT_FILE" 2>/dev/null
        if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
            echo "💾 تم حفظ الصوت في: $OUTPUT_FILE"
            echo "🔊 يمكنك تشغيله بـ: open $OUTPUT_FILE (macOS) أو vlc $OUTPUT_FILE (Linux)"
        else
            echo "⚠️  فشل حفظ الصوت"
        fi
    fi
else
    echo "❌ خطأ في الطلب:"
    echo "$RESPONSE"
fi

# حذف الملف المؤقت
rm -f "$TEMP_AUDIO"
echo "🧹 تم حذف الملف المؤقت"

