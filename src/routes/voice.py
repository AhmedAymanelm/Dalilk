from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import google.generativeai as genai
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import io
import os
from pathlib import Path
from helper.config import get_settings
from routes.schemas.nlp import Search_Reqest
import base64
import logging

logger = logging.getLogger("uvicorn.error")

voice_router = APIRouter(
    prefix="/api/v1/voice",
    tags=["api_v1", "voice"]
)

# إعداد Gemini API للصوت - سيتم تهيئته في كل request
def get_gemini_model():
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # استخدام gemini-2.0-flash للصوت كـ input (يدعم Speech-to-Text)
    # gemini-2.5-flash-preview-tts للـ Text-to-Speech فقط (output)
    try:
        return genai.GenerativeModel('gemini-2.0-flash')
    except:
        try:
            return genai.GenerativeModel('gemini-2.5-flash')
        except:
            return genai.GenerativeModel('gemini-2.5-pro')

# إعداد ElevenLabs - سيتم تهيئته من request
def get_eleven_client():
    settings = get_settings()
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY غير موجود في الإعدادات")
    return ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)


@voice_router.post("/speech-to-text")
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
        
        # الحصول على نموذج Gemini
        gemini_model = get_gemini_model()
        
        # رفع الملف لـ Gemini
        audio_file = genai.upload_file(path=temp_path)
        
        # تحويل الصوت لنص
        prompt = "استمع للتسجيل الصوتي وحوله لنص بالعربية بدقة:"
        response = gemini_model.generate_content([prompt, audio_file])
        
        # حذف الملف المؤقت
        Path(temp_path).unlink(missing_ok=True)
        
        transcript = response.text.strip()
        
        return JSONResponse(content={
            "success": True,
            "transcript": transcript
        })
    
    except Exception as e:
        logger.error(f"خطأ في تحويل الصوت: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في تحويل الصوت: {str(e)}")


@voice_router.post("/text-to-speech")
async def text_to_speech(text: str, voice_id: str = "Xb7hH8MSUJpSbSDYk0k2"):
    """
    تحويل النص إلى صوت باستخدام ElevenLabs
    voice_id: معرف الصوت (استخدم صوت عربي من ElevenLabs)
    """
    try:
        # الحصول على ElevenLabs client
        eleven_client = get_eleven_client()
        
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
        logger.error(f"خطأ في تحويل النص لصوت: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في تحويل النص لصوت: {str(e)}")


@voice_router.post("/voice-chat")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = None,
    limit: int = 5
):
    """
    معالجة كاملة: صوت -> نص -> رد من RAG -> صوت
    يتكامل مع نظام الـ RAG الموجود
    """
    try:
        # 1. تحويل الصوت لنص
        audio_data = await audio.read()
        
        # حفظ مؤقت
        temp_path = f"temp_voice_{audio.filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        # الحصول على نموذج Gemini
        gemini_model = get_gemini_model()
        
        # رفع الملف لـ Gemini
        audio_file = genai.upload_file(path=temp_path)
        
        # تحويل الصوت لنص مع retry
        prompt = "استمع للتسجيل الصوتي وحوله لنص بالعربية بدقة:"
        
        max_retries = 3
        response = None
        import time
        import re
        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content([prompt, audio_file])
                break
            except Exception as e:
                error_str = str(e).lower()
                if ("quota" in error_str or "429" in error_str) and attempt < max_retries - 1:
                    # استخراج وقت الانتظار من الرسالة
                    wait_time = 30  # افتراضي
                    wait_match = re.search(r'retry in ([\d.]+)s', str(e), re.IGNORECASE)
                    if wait_match:
                        wait_time = int(float(wait_match.group(1))) + 2  # أضف ثانيتين إضافيتين
                    
                    logger.warning(f"Quota exceeded, انتظار {wait_time} ثانية... (محاولة {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise
        
        if not response:
            Path(temp_path).unlink(missing_ok=True)
            raise HTTPException(status_code=429, detail="تم تجاوز الحد المسموح من الـ API. الرجاء المحاولة لاحقاً")
        
        # حذف الملف المؤقت
        Path(temp_path).unlink(missing_ok=True)
        
        transcript = response.text.strip()
        
        if not transcript:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "لم يتم التعرف على النص من الصوت"
                }
            )
        
        # 2. استخدام نظام الـ RAG الموجود للحصول على رد
        from controlles.NLPController import NLPController
        from models.ProjectModel import ProjectModels
        
        DEFAULT_PROJECT_ID = "default"
        
        # الحصول على NLP Controller من app
        nlp_controller = request.app.nlp_controller
        
        # الحصول على المشروع
        project_model = await ProjectModels.create_instans(
            db_client=request.app.mongodb,
        )
        project = await project_model.get_project_or_create_one(
            project_id=DEFAULT_PROJECT_ID
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")
        
        # استخدام NLP Controller للحصول على الرد
        session_id = session_id or DEFAULT_PROJECT_ID
        answer, full_prompt, chat_history, retrieved_docs = nlp_controller.Anser_Rag_question(
            project_id=DEFAULT_PROJECT_ID,
            message=transcript,
            session_id=session_id,
            top_k=limit or 5
        )
        
        if not answer:
            raise HTTPException(status_code=500, detail="لم يتم الحصول على رد من النظام")
        
        bot_response_text = answer.strip()
        
        # جلب بيانات السيارات من retrieved_docs (مثل ما في nlp.py)
        cars = []
        try:
            from models.AssetModel import AssetModel
            assets_model = await AssetModel.create_instans_Assets(db_client=request.app.mongodb)
            project_files = await assets_model.get_all_asset(asset_project_id=project.id, asset_type="file")
            
            all_cars_data = []
            for file_record in project_files:
                file_name = getattr(file_record, 'asset_name', None) or file_record.get('asset_name')
                if file_name:
                    import json
                    file_path = os.path.join("assets/files", DEFAULT_PROJECT_ID, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_cars_data = json.load(f)
                            break
            
            # Match retrieved docs with full car data
            def normalize_for_match(text: str) -> str:
                if not text:
                    return ""
                import re
                text = re.sub(r'[إأآا]', 'ا', text)
                text = text.replace('ى', 'ي').replace('ة', 'ه')
                text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
                return text.strip().lower()

            added_car_ids = set()
            
            for doc in retrieved_docs:
                rag_content = getattr(doc, "text", None) or getattr(doc, "page_content", None)
                if not rag_content:
                    continue

                normalized_doc = normalize_for_match(rag_content)

                for car in all_cars_data:
                    car_id = car.get('id')
                    if car_id in added_car_ids:
                        continue
                        
                    car_name = car.get('name', '')
                    car_rag = car.get('rag_content', '')
                    
                    normalized_name = normalize_for_match(car_name)
                    normalized_car = normalize_for_match(car_rag)
                    
                    car_price = car.get('price', '')
                    
                    is_match = (
                        (normalized_name and normalized_name[:50] in normalized_doc) or
                        (normalized_car and normalized_doc[:80] == normalized_car[:80]) or
                        (car_price and car_price in rag_content and normalized_name[:30] in normalized_doc)
                    )
                    
                    if is_match:
                        specs = car.get("specs") or car.get("structured_details", {})
                        car_with_score = {
                            "name": car.get("name"),
                            "price": car.get("price"),
                            "rating": car.get("rating"),
                            "id": car_id,
                            "images": car.get("images", []),
                            "specs": specs,
                            "rating_text": car.get("rating_text"),
                            "score": getattr(doc, "score", None),
                        }
                        cars.append(car_with_score)
                        added_car_ids.add(car_id)
                        break
        except Exception as e:
            logger.error(f"Error loading car data: {e}")
        
        if not bot_response_text:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "لم يتم الحصول على رد من النظام"
                }
            )
        
        # 3. تحويل الرد لصوت
        eleven_client = get_eleven_client()
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=bot_response_text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            )
        )
        
        audio_bytes = b""
        for chunk in audio_stream:
            audio_bytes += chunk
        
        # تحويل الصوت لـ base64 للإرجاع في JSON
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return JSONResponse(content={
            "success": True,
            "transcript": transcript,
            "response_text": bot_response_text,
            "cars": cars,
            "audio_base64": audio_base64,
            "audio_format": "mp3"
        })
    
    except Exception as e:
        logger.error(f"خطأ في voice chat: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ: {str(e)}")


@voice_router.post("/voice-chat-stream")
async def voice_chat_stream(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = None,
    limit: int = 5
):
    """
    معالجة كاملة مع إرجاع الصوت كـ stream مباشر
    """
    try:
        # 1. تحويل الصوت لنص
        audio_data = await audio.read()
        
        temp_path = f"temp_voice_{audio.filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        # الحصول على نموذج Gemini مع retry
        gemini_model = get_gemini_model()
        
        audio_file = genai.upload_file(path=temp_path)
        prompt = "استمع للتسجيل الصوتي وحوله لنص بالعربية بدقة:"
        
        max_retries = 3
        response = None
        import time
        import re
        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content([prompt, audio_file])
                break
            except Exception as e:
                error_str = str(e).lower()
                if ("quota" in error_str or "429" in error_str) and attempt < max_retries - 1:
                    # استخراج وقت الانتظار من الرسالة
                    wait_time = 30  # افتراضي
                    wait_match = re.search(r'retry in ([\d.]+)s', str(e), re.IGNORECASE)
                    if wait_match:
                        wait_time = int(float(wait_match.group(1))) + 2  # أضف ثانيتين إضافيتين
                    
                    logger.warning(f"Quota exceeded, انتظار {wait_time} ثانية... (محاولة {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise
        
        Path(temp_path).unlink(missing_ok=True)
        
        transcript = response.text.strip()
        
        if not transcript:
            raise HTTPException(status_code=400, detail="لم يتم التعرف على النص من الصوت")
        
        # 2. استخدام نظام الـ RAG الموجود
        from controlles.NLPController import NLPController
        from models.ProjectModel import ProjectModels
        
        DEFAULT_PROJECT_ID = "default"
        
        nlp_controller = request.app.nlp_controller
        
        project_model = await ProjectModels.create_instans(
            db_client=request.app.mongodb,
        )
        project = await project_model.get_project_or_create_one(
            project_id=DEFAULT_PROJECT_ID
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="المشروع غير موجود")
        
        session_id = session_id or DEFAULT_PROJECT_ID
        answer, full_prompt, chat_history, retrieved_docs = nlp_controller.Anser_Rag_question(
            project_id=DEFAULT_PROJECT_ID,
            message=transcript,
            session_id=session_id,
            top_k=limit or 5
        )
        
        if not answer:
            raise HTTPException(status_code=500, detail="لم يتم الحصول على رد من النظام")
        
        bot_response_text = answer.strip()
        
        # 3. تحويل الرد لصوت وإرجاعه كـ stream
        eleven_client = get_eleven_client()
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=bot_response_text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            )
        )
        
        audio_bytes = b""
        for chunk in audio_stream:
            audio_bytes += chunk
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=response.mp3",
                "X-Transcript": transcript,
                "X-Response-Text": bot_response_text
            }
        )
    
    except Exception as e:
        logger.error(f"خطأ في voice chat stream: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ: {str(e)}")

