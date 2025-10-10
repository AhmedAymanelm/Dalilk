from .BaseControlls import BaseControlls
from fastapi import FastAPI, APIRouter, Depends, UploadFile
from models.Enums import ResponseStatus
import os


class ProjectControllers(BaseControlls):
    def __init__(self):
        super().__init__()
    
    def get_project_path(self,project_id: str):
        project_dir = os.path.join(self.file_dir,project_id) 
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        return project_dir
    
         