from fastapi import FastAPI,  APIRouter, status , Request
from fastapi.responses import JSONResponse
from routes.schemas.nlp import Push_Request , Search_Reqest
from models.ProjectModel import ProjectModels
from models.ChunkModels import ChunkModel
from models.AssetModel import AssetModel
from controlles import NLPController
from bson.objectid import ObjectId
from models.db_schemas.data_Chunks import DataChunk
import json
import os
import uuid

from models.Enums import ResponseStatus
import logging

logger = logging.getLogger("uvicorn.error")

DEFAULT_PROJECT_ID = "default"

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_1","nlp"]
)

@nlp_router.post("/index/push")
async def index_project(request: Request, push_request: Push_Request):
    project_id = DEFAULT_PROJECT_ID

    # Models
    project_model = await ProjectModels.create_instans(
        db_client=request.app.mongodb,
    )
    chunk_model = await ChunkModel.create_instans(
        db_client=request.app.mongodb,
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )
    
    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "Signal": ResponseStatus.PROJECT_NOT_FOUND.value,
            },
        )
    
    project_object_id = project.id

    total_chunks = await chunk_model.collection.count_documents(
        {"Chunk_project_id": project_object_id}
    )
    
    print(f"Total chunks for project {project_id}: {total_chunks}")
    
    if total_chunks == 0:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "Signal": "no_chunks_found",
                "message": f"No chunks found"
            },
        )
    
    # NLP Controller
    nlp_controller = NLPController(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vector_db_client=request.app.vector_db_client,
        template_parser=request.app.template_parser,
    )

    # Pagination
    has_record = True
    page_no = 1
    inserted_item_count = 0
    
    while has_record:
        page_chunks = await chunk_model.get_project_chunks(
            project_id=project_object_id,
            page_no=page_no
        )
        
        if not page_chunks or len(page_chunks) == 0:
            has_record = False
            break
        
        print(f"Page {page_no}: Processing {len(page_chunks)} chunks")
        page_no += 1

        is_inserted = nlp_controller.index_into_vectordb(
            project=project,
            chunks_list=page_chunks,
            do_reset=push_request.do_reset,
        )
        
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "Signal": ResponseStatus.INSERT_INTO_VECTOR_DB_FAILED.value,
                }
            )
        
        inserted_item_count += len(page_chunks)

    return JSONResponse(
        content={
            "Signal": ResponseStatus.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "Inserted Item Count": inserted_item_count
        },
    )

@nlp_router.get("/index/info")
async def get_project_index_info(request: Request):
    project_id = DEFAULT_PROJECT_ID
    project_model = await ProjectModels.create_instans(
        db_client=request.app.mongodb,
    )


    project = await project_model.get_project_or_create_one(
        project_id=project_id
        )
    
    nlp_controller = NLPController(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vector_db_client=request.app.vector_db_client,
        template_parser =request.app.template_parser,
    )

    collection_info = nlp_controller.get_collection_info(project=project)
    return JSONResponse(
        content={
            "Signal": ResponseStatus.VECTORDB_COLLECTION_SUCCESS.value,
            "Collection Info": collection_info
            },
    ) 



@nlp_router.post("/index/search")
async def search_project(
    request: Request,
    search_request: Search_Reqest
):
    project_id = DEFAULT_PROJECT_ID
    try:

        project_model = await ProjectModels.create_instans(
            db_client=request.app.mongodb,
        )

        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )

        nlp_controller = NLPController(
            generation_client=request.app.generation_client,
            embedding_client=request.app.embedding_client,
            vector_db_client=request.app.vector_db_client,
            template_parser =request.app.template_parser,
        )
        
        results = nlp_controller.search_in_vectordb(
            project_id=project_id,
            message=search_request.message,  
            top_k=search_request.limit or 5  

        )
        
        return JSONResponse(content={
            "Signal": "search_success",
            "results": [result.dict() for result in results]
        })
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Signal": "search_failed",
                "error": str(e)
            }
        )


@nlp_router.post("/index/chat")
async def Chat_project(request: Request, search_request: Search_Reqest):
    # Retrieve Project
    project_id = DEFAULT_PROJECT_ID
    project_model = await ProjectModels.create_instans(db_client=request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id=project_id.strip())
   
    nlp_controller = request.app.nlp_controller
    
    # Session
    session_id = search_request.session_id or f"session_{uuid.uuid4().hex[:12]}"
    
    # 🔥 Pre-calculate Requested Brand (Global Scope Fix)
    requested_brand = None
    try:
        known_brands_list = [
            'mg', 'byd', 'تويوتا', 'هيونداي', 'مرسيدس', 'بي ام', 'bmw',
            'بورش', 'porsche', 'فيراري', 'ferrari', 'لامبورجيني', 'lamborghini',
            'بنتلي', 'bentley', 'رولز', 'rolls', 'اودي', 'audi',
            'نيسان', 'nissan', 'كيا', 'kia', 'فورد', 'ford',
            'جينيسيس', 'genesis', 'كوبرا', 'cupra',
            'بيجو', 'peugeot', 'شيري', 'chery', 'جيلى', 'جيلي', 'geely',
            'سوزوكي', 'suzuki', 'ميتسوبيشي', 'mitsubishi', 'سكودا', 'skoda',
            'سوبارو', 'subaru', 'هوندا', 'honda', 'مازدا', 'mazda',
            'سيتروين', 'citroen', 'رينو', 'renault', 'جيب', 'jeep', 
            'اوبل', 'opel', 'ام جى', 'ام جي', 'لادا', 'فيات', 'fiat'
        ]
        msg_lower = (search_request.message or "").lower()
        for b in known_brands_list:
            if b in msg_lower:
                if b in ['بي ام', 'bmw']: b = 'bmw'
                if b in ['ام جى', 'ام جي']: b = 'mg'
                requested_brand = b
                break
    except: pass

    # 1. Retrieval
    answer, full_prompt, chat_history, retrieved_docs = nlp_controller.Anser_Rag_question(
        project_id=project_id,
        message=search_request.message,
        session_id=session_id,  
        top_k=search_request.limit or 5
    )
    
    if not answer:
        return JSONResponse(status_code=500, content={"Signal": "search_failed", "error": "No answer"})

    # Helpers for Display Logic
    def is_off_topic(ans, msg):
        ans_start = (ans or "")[:100].lower() # Check start of answer usually contains refusal
        refusal_phrases = [
            "دليلك", "مساعد ذكي", "متخصص في", # Usually "ana dalilak..."
            "مقدرش", "آسف", "اسف", "لا استطيع", "لا أستطيع",
            "خارج تخصصي", "بس عربيات", "فقط بالسيارات",
            "not able to help", "only cars"
        ]
        # If answer is short and contains refusal, it's off topic
        if len(ans) < 200 and any(p in ans_start for p in refusal_phrases):
            return True
        return False

    def is_greeting(msg):
        msg = (msg or "").lower().strip()
        greetings = ["hi", "hello", "hola", "welcome", "ازيك", "عامل ايه", "سلام عليكم", "مرحبا", "هلا", "صباح", "مساء"]
        if len(msg.split()) < 4 and any(g in msg for g in greetings):
            return True
        return False

    # 2. Extract Cars (Only if relevant)
    cars = []
    should_show_cars = retrieved_docs and not is_off_topic(answer, search_request.message) and not is_greeting(search_request.message)
    
    if should_show_cars:
        try:
            # DEBUG LOG ENTRY
            try:
                with open("debug_car_loading.txt", "w") as f: 
                    f.write(f"START. Docs={len(retrieved_docs)}\n")
            except: pass

            # Load Data
            assets_model = await AssetModel.create_instans_Assets(db_client=request.app.mongodb)
            project_files = await assets_model.get_all_asset(asset_project_id=project.id, asset_type="file")
            
            all_cars = []
            
            # FILE LOG
            try:
                with open("debug_car_loading.txt", "a") as f:
                    f.write(f"Project files: {len(project_files)}\n")
            except: pass
            
            def safe_load(path):
                if os.path.exists(path):
                     try: 
                        with open(path, 'r', encoding='utf-8') as f: 
                            d = json.load(f)
                            # logger.info(f"Loaded {len(d)} items from {path}")
                            return d if isinstance(d, list) else []
                     except Exception as e:
                        logger.error(f"Failed to load {path}: {e}")
                else:
                    logger.warning(f"Path not found: {path}")
                return []

            # Load from DB assets
            for rec in project_files:
                # Handle both object and dict
                fname = getattr(rec, 'asset_name', None)
                if not fname and hasattr(rec, 'get'):
                     fname = rec.get('asset_name')
                
                # FILE LOG Record
                try:
                    with open("debug_car_loading.txt", "a") as f:
                        f.write(f"Record: {rec}, Fname extracted: {fname}\n")
                except: pass

                if fname:
                    path = os.path.join("assets/files", project_id, fname)
                    # FILE LOG
                    try:
                        with open("debug_car_loading.txt", "a") as f:
                            f.write(f"Loop DB Asset. Fname: {fname}, Path: {path}, Exists: {os.path.exists(path)}\n")
                    except: pass
                    
                    all_cars.extend(safe_load(path))
            
            # FORCE Directory Scan (Always)
            pdir = os.path.join("assets/files", project_id)
            
            # DEBUG LOG TO FILE
            try:
                with open("debug_car_loading.txt", "w") as f:
                    f.write(f"CWD: {os.getcwd()}\n")
                    f.write(f"Target Dir: {os.path.abspath(pdir)}\n")
                    f.write(f"Exists: {os.path.exists(pdir)}\n")
                    if os.path.exists(pdir):
                        f.write(f"Contents: {os.listdir(pdir)}\n")
            except: pass

            if os.path.exists(pdir):
                logger.info(f"Scanning directory: {pdir}")
                for f in os.listdir(pdir):
                    if f.endswith(".json"):
                        path = os.path.join(pdir, f)
                        all_cars.extend(safe_load(path))

            # Deduplicate
            cars_map = {str(c.get('id')): c for c in all_cars if c.get('id')}
            cars_list = list(cars_map.values())

            # Match
            from difflib import SequenceMatcher
            import re
            
            def norm(t): 
                return re.sub(r'[^\w]', '', t or "").lower()

            if requested_brand:
                logger.info(f"🔒 Strict Brand Filter Enabled: {requested_brand}")

            added = set()
            for doc in retrieved_docs:
                txt = getattr(doc, "text", "") or getattr(doc, "page_content", "")
                if not txt: continue
                
                txt_norm = norm(txt)
                best_c = None
                best_s = 0
                
                for c in cars_list:
                    if str(c.get('id')) in added: continue
                    
                    c_name = c.get('name', '')
                    c_name_norm = norm(c_name)
                    
                    # 🔥 Apply Brand Filter Check
                    if requested_brand:
                        # Special handling for translated names if needed, but usually fuzzy match helps.
                        # We check if the standardized brand name is part of the car name (normalized)
                        
                        # Fix for MG/Porsche/Peugeot mixups:
                        brand_checks = [requested_brand]
                        if requested_brand == 'mg': brand_checks.extend(['ام جى', 'ام جي'])
                        if requested_brand == 'porsche': brand_checks.extend(['بورش'])
                        if requested_brand == 'peugeot': brand_checks.extend(['بيجو'])
                        
                        # If car name doesn't contain ANY of the brand variants, SKIP IT.
                        is_brand_match = False
                        for b_chk in brand_checks:
                            if b_chk in c_name.lower():
                                is_brand_match = True
                                break
                        
                        if not is_brand_match:
                            continue

                    # Score based on overlap
                    c_rag = norm(c.get('rag_content', ''))
                    c_name = norm(c.get('name', ''))
                    
                    s = 0
                    # Exact start match (very strong)
                    if c_rag and txt_norm.startswith(c_rag[:40]): s = 100
                    # Name matches
                    elif c_name and c_name in txt_norm: s = 90
                    # Fuzzy
                    elif c_name:
                        # Check partial name overlap
                        common = SequenceMatcher(None, c_name, txt_norm).find_longest_match(0, len(c_name), 0, len(txt_norm))
                        if common.size > 5: s = 50 + common.size

                    if s > best_s:
                        best_s = s
                        best_c = c
                
                if best_c and best_s > 60:
                    added.add(str(best_c.get('id')))
                    
                    # Add match_score for sorting
                    car_obj = {
                        "name": best_c.get("name"),
                        "price": best_c.get("price"),
                        "rating": best_c.get("rating"),
                        "id": best_c.get("id"),
                        "images": best_c.get("images", []),
                        "specs": best_c.get("structured_details") or best_c.get("specs") or {},
                        "rating_text": best_c.get("rating_text"),
                        "score": getattr(doc, "score", None),
                        "match_score": best_s
                    }
                    cars.append(car_obj)

        except Exception as e:
            logger.error(f"Car extraction error: {e}")

    # Sort cars by match accuracy (Highest score first)
    cars.sort(key=lambda x: x.get('match_score', 0), reverse=True)

    # Final Check: If cars found but LLM says "not available", FORCE positive response
    if cars:
        negatives = ["مش متاحة", "غير متوفرة", "مفيش", "لا يوجد", "للأسف", "للاسف"]
        
        placeholders = ["[اسم العربية", "[السعر]", "[اسم السيارة]", "اسم العربية"]
        has_placeholders = any(p in answer for p in placeholders)
        
        is_negative = any(n in answer for n in negatives)
        
        if has_placeholders or (len(answer) < 100 and is_negative):
             # Rebuild the answer using REAL data
             top_cars = cars[:4] # Take top 4
             cars_text = "\n".join([f"- {c['name']} ({c['price']})" for c in top_cars])
             answer = f"لقيت لك مجموعة ممتازة تناسب طلبك! 🚗\n\n{cars_text}\n\nشوف التفاصيل والصور في الكروت تحت 👇"
        
        elif is_negative:
             # Just prepend a positive confirmation
             answer = f"موجود طلبك! ✨ \n" + answer.replace("مش متاحة", "متاحة").replace("غير متوفرة", "متوفرة")
    
    # CASE: No cars found, but LLM is hallucinating placeholders
    else:
        placeholders = ["[اسم العربية", "[السعر]", "[اسم السيارة]", "اسم العربية"]
        if any(p in answer for p in placeholders):
            answer = "للأسف مش لاقي عربيات متاحة حالياً بالمواصفات دي في قاعدة البيانات. ممكن تحاول تغير نطاق الميزانية أو تدور على ماركة تانية؟"

    # Limit output to max 5 cars as requested
    cars = cars[:5]
    
    # 🔥 Final Sanity Checks
    
    # 1. Brand Mismatch Fix
    if requested_brand and len(cars) == 0:
        answer = f"للأسف مفيش عربيات {requested_brand} متاحة حالياً في قاعدة البيانات."
    
    # 2. General Empty Cars Fix (if LLM is talking about cars but we have none)
    elif len(cars) == 0 and retrieved_docs:
        # If we searched (retrieved_docs exists) but found nothing, and LLM is babbling about cars
        # Check if answer mentions car-related words
        car_keywords = ["عربية", "سيارة", "عندك", "متاح", "بسعر", "جنيه", "موديل"]
        if any(k in answer for k in car_keywords):
            # LLM is hallucinating about cars that don't exist
            if requested_brand:
                answer = f"للأسف مفيش عربيات {requested_brand} متاحة حالياً."
            else:
                answer = "للأسف مفيش عربيات متاحة حالياً بالمواصفات دي. ممكن تجرب تغير الميزانية أو تسأل عن ماركة تانية؟"

    return JSONResponse(content={
        "success": True, 
        "message": answer, 
        "cars": cars, 
        "session_id": session_id,
        "debug_retrieved": len(retrieved_docs) if retrieved_docs else 0,
        "debug_loaded_cars": len(all_cars_list) if 'all_cars_list' in locals() else 0
    })
   