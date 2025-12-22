"""
حل بديل باستخدام Whisper للـ Speech-to-Text
بدلاً من Gemini (لتجنب مشاكل الـ quota)
"""

from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import whisper
import io
import os
from pathlib import Path
from helper.config import get_settings
from routes.schemas.nlp import Search_Reqest
import base64
import logging
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

logger = logging.getLogger("uvicorn.error")

voice_whisper_router = APIRouter(
    prefix="/api/v1/voice-whisper",
    tags=["api_v1", "voice"]
)

# تحميل نموذج Whisper (مرة واحدة)
_whisper_model = None

def get_whisper_model():
    """الحصول على نموذج Whisper (يتم تحميله مرة واحدة)"""
    global _whisper_model
    if _whisper_model is None:
        logger.info("جاري تحميل نموذج Whisper (small - دقة أعلى)...")
        _whisper_model = whisper.load_model("small")  # base, small, medium, large (small = دقة أفضل)
        logger.info("✅ تم تحميل نموذج Whisper")
    return _whisper_model

# إعداد ElevenLabs
def get_eleven_client():
    settings = get_settings()
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY غير موجود في الإعدادات")
    return ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)


@voice_whisper_router.post("/speech-to-text")
async def speech_to_text_whisper(audio: UploadFile = File(...)):
    """
    تحويل الصوت إلى نص باستخدام Whisper (بدون quota limits)
    """
    try:
        # قراءة ملف الصوت
        audio_data = await audio.read()
        
        # حفظ مؤقت
        temp_path = f"temp_whisper_{audio.filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        # استخدام Whisper
        model = get_whisper_model()
        result = model.transcribe(temp_path, language="ar")
        
        # حذف الملف المؤقت
        Path(temp_path).unlink(missing_ok=True)
        
        transcript = result["text"].strip()
        
        return JSONResponse(content={
            "success": True,
            "transcript": transcript
        })
    
    except Exception as e:
        logger.error(f"خطأ في تحويل الصوت: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في تحويل الصوت: {str(e)}")


@voice_whisper_router.post("/voice-chat")
async def voice_chat_whisper(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = None,
    limit: int = 5
):
    """
    معالجة كاملة باستخدام Whisper: صوت -> نص -> رد من RAG -> صوت
    """
    try:
        # 1. تحويل الصوت لنص باستخدام Whisper
        audio_data = await audio.read()
        
        temp_path = f"temp_whisper_{audio.filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        model = get_whisper_model()
        result = model.transcribe(temp_path, language="ar")
        transcript = result["text"].strip()
        
        Path(temp_path).unlink(missing_ok=True)
        
        if not transcript:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "لم يتم التعرف على النص من الصوت"
                }
            )
        
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
        
        # جلب بيانات السيارات من retrieved_docs (مثل ما في voice.py)
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

