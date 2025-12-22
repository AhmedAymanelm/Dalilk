"""
ملاحظة: تم دمج هذا الكود في routes/voice.py وربطه مع نظام الـ RAG الموجود
يمكنك استخدام endpoints التالية:
- POST /api/v1/voice/speech-to-text
- POST /api/v1/voice/text-to-speech  
- POST /api/v1/voice/voice-chat (يتكامل مع RAG)
- POST /api/v1/voice/voice-chat-stream

هذا الملف محفوظ للرجوع إليه فقط.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import google.generativeai as genai
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import io
import os
from pathlib import Path

app = FastAPI()

# إعداد Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# إعداد ElevenLabs
eleven_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# نموذج Gemini
model = genai.GenerativeModel('gemini-2.5-flash-preview-tts')

# نظام الشات بوت (System Prompt)
SYSTEM_PROMPT = """
أنت مساعد ذكي متخصص في ترشيح السيارات للعملاء في مصر.
مهمتك مساعدة العملاء في اختيار السيارة المناسبة حسب:
- الميزانية
- نوع الاستخدام (عائلي، رياضي، اقتصادي)
- عدد الركاب
- استهلاك الوقود
- الماركة المفضلة

قدم ترشيحات واضحة ومختصرة مع ذكر الأسعار التقريبية.
"""


@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    تحويل الصوت إلى نص باستخدام Gemini
    """
    try:
        # قراءة ملف الصوت
        audio_data = await audio.read()
        
        # حفظ مؤقت
        temp_path = f"temp_{audio.filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        # رفع الملف لـ Gemini
        audio_file = genai.upload_file(path=temp_path)
        
        # تحويل الصوت لنص
        prompt = "استمع للتسجيل الصوتي وحوله لنص بالعربية بدقة:"
        response = model.generate_content([prompt, audio_file])
        
        # حذف الملف المؤقت
        Path(temp_path).unlink(missing_ok=True)
        
        transcript = response.text.strip()
        
        return {
            "success": True,
            "transcript": transcript
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تحويل الصوت: {str(e)}")


@app.post("/chat")
async def chat(user_message: str):
    """
    معالجة رسالة المستخدم والحصول على رد الشات بوت
    """
    try:
        # إنشاء المحادثة مع النظام
        full_prompt = f"{SYSTEM_PROMPT}\n\nالمستخدم: {user_message}\n\nالرد:"
        
        response = model.generate_content(full_prompt)
        bot_response = response.text.strip()
        
        return {
            "success": True,
            "user_message": user_message,
            "bot_response": bot_response
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الرسالة: {str(e)}")


@app.post("/text-to-speech")
async def text_to_speech(text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB"):
    """
    تحويل النص إلى صوت باستخدام ElevenLabs
    voice_id: معرف الصوت (استخدم صوت عربي من ElevenLabs)
    """
    try:
        # توليد الصوت
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",  # يدعم العربية
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            )
        )
        
        # تحويل الـ stream لـ bytes
        audio_bytes = b""
        for chunk in audio_stream:
            audio_bytes += chunk
        
        # إرجاع الصوت
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=response.mp3"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تحويل النص لصوت: {str(e)}")


@app.post("/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    معالجة كاملة: صوت -> نص -> رد -> صوت
    """
    try:
        # 1. تحويل الصوت لنص
        stt_result = await speech_to_text(audio)
        transcript = stt_result["transcript"]
        
        # 2. معالجة النص والحصول على رد
        chat_result = await chat(transcript)
        bot_response = chat_result["bot_response"]
        
        # 3. تحويل الرد لصوت
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            text=bot_response,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
            )
        )
        
        audio_bytes = b""
        for chunk in audio_stream:
            audio_bytes += chunk
        
        return {
            "success": True,
            "transcript": transcript,
            "response_text": bot_response,
            "audio_base64": io.BytesIO(audio_bytes).getvalue()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)