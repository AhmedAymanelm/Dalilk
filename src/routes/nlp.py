from fastapi import FastAPI,  APIRouter, status , Request
from fastapi.responses import JSONResponse
from routes.schemas.nlp import Push_Request , Search_Reqest
from models.ProjectModel import ProjectModels
from models.ChunkModels import ChunkModel
from controlles import NLPController
from models.Enums import ResponseStatus
import logging

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_1","nlp"]
)

@nlp_router.post("/index/push/{project_id}")

async def index_project(project_id:str, request: Request,push_request:Push_Request):
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
    
    nlp_controller = NLPController(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vector_db_client=request.app.vector_db_client,
    )

    has_record = True
    page_no = 1
    inserted_item_count = 0
    idx = 0
    while has_record:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.project_id,page_no=page_no)
        
        if not page_chunks or len(page_chunks) == 0:
            has_record = False
            break
            
        page_no += 1

        chunks_ids = list(range(idx, idx+len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_into_vectordb(
            project=project,
            chunk=page_chunks,
            do_reset=push_request.do_reset,
            chunks_ids=chunks_ids,
            )
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "Signal": ResponseStatus.INSERT_INTO_VECTOR_DB_FAILED.value,
                })
        
        inserted_item_count += len(page_chunks)


    return JSONResponse(
        content={
            "Signal": ResponseStatus.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "Inserted Item Count": inserted_item_count
            },
    )

    # chunks = chunk_model.get_project_chunks(project_id=project.project_id)



@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info (project_id:str, request: Request):

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
    )

    collection_info = nlp_controller.get_collection_info(project=project)
    return JSONResponse(
        content={
            "Signal": ResponseStatus.VECTORDB_COLLECTION_SUCCESS.value,
            "Collection Info": collection_info
            },
    ) 



@nlp_router.post("/index/search/{project_id}")
async def search_index (project_id:str, request: Request, search_request:Search_Reqest):
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
    )

    search_result = nlp_controller.search_in_vectordb(
        project=project, 
        text=search_request.text,
        limit=search_request.limit)
    
    if not search_result:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Signal": ResponseStatus.VECTOR_DB_SEARCH_ERORR.value,
            })
    
    return JSONResponse(
            
            content={
                "Signal": ResponseStatus.VECTOR_DB_SEARCH_SUCCESS .value,
            })
    
    

