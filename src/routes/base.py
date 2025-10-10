from fastapi import FastAPI, APIRouter, Depends
import os
from helper.config import Settings, get_settings
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)

@base_router.get("/")
async def Welcome(app_settings: Settings = Depends(get_settings)):

    app_name = get_settings().APP_NAME
    app_version = get_settings().APP_VERSION
    return {
        "message": f"Welcome to {app_name}, here you can do everything"
        }
