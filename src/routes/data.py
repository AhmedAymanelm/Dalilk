from fastapi import APIRouter, Depends, UploadFile , status , Request
from fastapi.responses import JSONResponse
from helper.config import Settings, get_settings
from controlles import DataControlles , ProjectControllers , ProcessControlles
from models.Enums import ResponseStatus
from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helper.config import Settings, get_settings
from controlles import DataControlles, ProjectControllers, ProcessControlles
from models.Enums import ResponseStatus
import os
import logging
import aiofiles
from bson.objectid import ObjectId
from routes.schemas.data_schemas import ProcessReqest
from models.ProjectModel import ProjectModels
from models.ChunkModels import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemas.data_Chunks import DataChunk
from models.db_schemas.assets import Asset
from models.Enums import AssetstypeEnums

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])

# Default project ID - ثابت لكل العمليات
DEFAULT_PROJECT_ID = "default"


@data_router.post("/upload")
async def upload_file(request: Request, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    project_id = DEFAULT_PROJECT_ID
    project_model = await ProjectModels.create_instans(db_client=request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    # Validate file type and size
    dataControlles = DataControlles()
    is_valid, results_signal = dataControlles.validate_Upload_file(file=file)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": results_signal})

    project_dir_path, _ = ProjectControllers().get_project_path(project_id=project_id), None
    # generate unique filepath (returns (file_location, file_id))
    file_location, file_id = dataControlles.genertate_uniqe_filepath(original_filename=file.filename, project_id=project_id)

    try:
        async with aiofiles.open(file_location, "wb") as out_file:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await out_file.write(chunk)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": ResponseStatus.FILE_UPLOAD_FAILE.value, "detail": str(e)})

    assets_model = await AssetModel.create_instans_Assets(db_client=request.app.mongodb)
    assets_resours = Asset(asset_project_id=project.id, asset_type=AssetstypeEnums.FILE.value, asset_name=file_id, asset_size=os.path.getsize(file_location))
    asset_record = await assets_model.create_asset(asset=assets_resours)

    return JSONResponse(content={"status": ResponseStatus.UpLOAD_SUCCESS.value, "file_id": str(asset_record.id)})


# Create endpoint process data
@data_router.post("/process")
async def process_endpoint(request: Request, process_request: ProcessReqest):
    project_id = DEFAULT_PROJECT_ID
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.overlap
    do_reset = process_request.do_reset

    project_model = await ProjectModels.create_instans(db_client=request.app.mongodb)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    assets_model = await AssetModel.create_instans_Assets(db_client=request.app.mongodb)

    project_file_ids = []
    if process_request.file_id:
        asset_record = await assets_model.get_asset_record(
            asset_project_id=project.id,
            asset_name=process_request.file_id,
        )
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": ResponseStatus.NOT_FOUND.value,
                    "detail": f"File '{process_request.file_id}' not found",
                },
            )

        # normalize id and name
        asset_id = getattr(asset_record, "id", None) or getattr(asset_record, "_id", None)
        asset_name = getattr(asset_record, "asset_name", None)
        project_file_ids.append((asset_id, asset_name))
    else:
       
        project_files = await assets_model.get_all_asset(asset_project_id=project.id, asset_type=AssetstypeEnums.FILE.value)

        for record in project_files:
            # extract asset id and name safely regardless of dict or object
            if isinstance(record, dict):
                asset_id = record.get("_id") or record.get("id")
                name = record.get("asset_name")
            else:
                asset_id = getattr(record, "id", None) or getattr(record, "_id", None)
                name = getattr(record, "asset_name", None)

            if name:
                project_file_ids.append((asset_id, name))

    if len(project_file_ids) == 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": ResponseStatus.BAD_REQUEST.value})

    process_controlles = ProcessControlles(project_id=project_id)
    no_f_records = 0
    no_f_file = 0

    # reset chunks
    chunk_model = await ChunkModel.create_instans(db_client=request.app.mongodb)
    if do_reset == 1:
        _ = await chunk_model.delete_chunk_by_project_id(project_id=ObjectId(project.id))

    for asset_id, file_id in project_file_ids:
        try:
            file_content = process_controlles.get_file_content(file_id=file_id)
        except Exception as e:
            logger.error(f"Error getting content for file '{file_id}': {e}")
            continue

        if file_content is None:
            logger.error(f"No content returned for file: {file_id}")
            continue

        try:
            file_chunks = process_controlles.split_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap)
            
        except Exception as e:
            logger.error(f"Error splitting file '{file_id}': {e}")
            continue

        if not file_chunks:
            logger.error(f"No chunks produced for file: {file_id}")
            continue

        file_chunks_record = [
            DataChunk(
                Chunk_text=chunk.page_content, 
                Chunk_metadata=chunk.metadata, 
                Chunk_order=i + 1,
                Chunk_project_id=project.id,
                Chunk_asset_id = asset_id
                )
            for i, chunk in enumerate(file_chunks)
        ]

        try:
            inserted = await chunk_model.insert_meny_chunk(chunks=file_chunks_record)
            no_f_records += inserted
            no_f_file += 1
        except Exception as e:
            logger.error(f"Failed to insert chunks for file '{file_id}': {e}")
            continue

    return JSONResponse(content={"status": ResponseStatus.PROCESSING_SUCCESS.value, "detail": f"{no_f_records} chunks inserted successfully", "Processed files": no_f_file})


     