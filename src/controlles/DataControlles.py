from .BaseControlls import BaseControlls
from fastapi import FastAPI, APIRouter, Depends, UploadFile
from models.Enums import ResponseStatus
from .ProjectControllers import ProjectControllers
from helper.config import Settings, get_settings
import os
import re
class DataControlles(BaseControlls):
    def __init__(self):
        super().__init__()
        self.scale_size = 1024 * 1024  # *  MB

    def validate_Upload_file(self,file: UploadFile):
        if file.content_type not in self.app_settings.FILE_TYPE:
            return False , ResponseStatus.INVALID_FILE_TYPE.value
        if file.size > self.app_settings.MAX_FILE_SIZE * self.scale_size:
            return False , ResponseStatus.FILE_SIZE_EXCEEDED.value
        return True  , ResponseStatus.SUCCESS.value


    def genertate_uniqe_filepath(self, original_filename: str, project_id: str):
        ext = os.path.splitext(original_filename)[1]
        rondom_file_name = self.genertate_random_string()
        project_path = ProjectControllers().get_project_path(project_id=project_id)
        clean_filename = self.get_clean_filename(original_filename=original_filename)
        new_filename = f"{rondom_file_name}_{clean_filename}"
        new_filepath = os.path.join(project_path, new_filename)
        
        while os.path.exists(new_filepath):
            rondom_file_name = self.genertate_random_string()
            new_filename = f"{rondom_file_name}_{clean_filename}{ext}"
            new_filepath = os.path.join(project_path, new_filename)
            
        return new_filepath, new_filename  # file_location, file_id

    def get_clean_filename(self, original_filename: str) :
        
        clean_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_filename)
        clean_filename = re.sub(r'\s+', '_', clean_filename)

        return clean_filename
    
       
    
    