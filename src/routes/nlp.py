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

from models.Enums import ResponseStatus
import logging

logger = logging.getLogger("uvicorn.error")

# Default project ID - ثابت لكل العمليات
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

    # جلب أو إنشاء المشروع
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

    # عدد الشانكس
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

        # إدخال الشانكس في الـ vector DB
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
    project_id = DEFAULT_PROJECT_ID
    project_model = await ProjectModels.create_instans(
        db_client=request.app.mongodb,
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id.strip()
    )

   
    nlp_controller = request.app.nlp_controller

    # Normalize user message for downstream heuristics
    user_message = (search_request.message or "").strip()

    session_id = search_request.session_id or project_id
    
    answer, full_prompt, chat_history, retrieved_docs = nlp_controller.Anser_Rag_question(
        project_id=project_id,
        message=search_request.message,
        session_id=session_id,  
        top_k=search_request.limit or 5
    )
    
    if not answer:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Signal": "search_failed",
                "error": "No answer found"
            }
        )

    # Small heuristic: لو السؤال توضيحي عن مفهوم (زي "حصان 214 يعني ايه؟")
    # ما نرجعش العربيات تاني، نخلي الرد نصي بس.
    def _is_concept_explanation_question(msg: str) -> bool:
        msg = msg or ""
        msg_norm = msg.replace("ييعني", "يعني")  # تصحيح شائع بسيط
        concept_keywords = [
            "يعني", "يعنى", "معنى", "ما هو", "ايه هو", "اي هو", "ماهي",
        ]
        spec_words = [
            "حصان", "عزم", "تورك", "cc", "سي سي", "قوة الموتور", "الهورس باور", "horsepower",
        ]
        return any(k in msg_norm for k in concept_keywords) and any(s in msg_norm for s in spec_words)

    # Build cars list from retrieved documents (whenever RAG is used),
    # إلا لو السؤال توضيحي عن مفهوم تقني.
    cars: list[dict] = []
    
    logger.info(f"Retrieved docs count: {len(retrieved_docs) if retrieved_docs else 0}")

    if retrieved_docs and not _is_concept_explanation_question(user_message):
        try:
            assets_model = await AssetModel.create_instans_Assets(db_client=request.app.mongodb)
            project_files = await assets_model.get_all_asset(asset_project_id=project.id, asset_type="file")
            
            logger.info(f"Project files count: {len(project_files) if project_files else 0}")

            all_cars_data = []
            for file_record in project_files:
                file_name = getattr(file_record, 'asset_name', None) or file_record.get('asset_name')
                if file_name:
                    file_path = os.path.join("assets/files", project_id, file_name)
                    logger.info(f"Checking file path: {file_path}, exists: {os.path.exists(file_path)}")
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_cars_data = json.load(f)
                            logger.info(f"Loaded {len(all_cars_data)} cars from file")
                            break
            
            logger.info(f"Total cars data loaded: {len(all_cars_data)}")

            # Match retrieved docs with full car data
            # Use flexible matching: check if car name appears in doc text
            def normalize_for_match(text: str) -> str:
                if not text:
                    return ""
                import re
                text = re.sub(r'[إأآا]', 'ا', text)
                text = text.replace('ى', 'ي').replace('ة', 'ه')
                text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
                return text.strip().lower()

            added_car_ids = set()  # Prevent duplicates
            
            for doc in retrieved_docs:
                rag_content = getattr(doc, "text", None) or getattr(doc, "page_content", None)
                logger.info(f"Doc text (first 100 chars): {rag_content[:100] if rag_content else 'None'}")
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
                        logger.info(f"MATCHED car: {car_name}")
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

    # إذا لم يوجد أي تطابق مع بيانات السيارات، اعرض كل retrieved_docs كما هي في cars
    if not cars and retrieved_docs and not _is_concept_explanation_question(user_message):
        for doc in retrieved_docs:
            doc_dict = {
                "text": getattr(doc, "text", None) or getattr(doc, "page_content", None),
                "score": getattr(doc, "score", None),
            }
            if hasattr(doc, "metadata") and doc.metadata:
                doc_dict["metadata"] = doc.metadata
            cars.append(doc_dict)

    return JSONResponse(content={
        "success": True if answer is not None else False ,
        "message": answer.strip(),
        "cars": cars,
    })

