from pydantic import BaseModel , Field, validator
from bson import ObjectId
from typing import Optional



class DataChunk(BaseModel):
    id : Optional[ObjectId] = Field(None, alias="_id") 

    Chunk_text : str = Field(..., min_length=1)
    Chunk_metadata : dict
    Chunk_order : int = Field(..., gt= 0) 
    Chunk_project_id :  ObjectId
    Chunk_asset_id : ObjectId



    class Config:
        arbitrary_types_allowed = True


    @classmethod
    def get_index(cls):
        return [
            {
                "key": [("Chunk_project_id", 1)],
                "name": "Chunk_project_id_index_1",
                "unique": False
            }
        ]
    

class RetrevedDecument(BaseModel):
    text : str 
    score : float



 