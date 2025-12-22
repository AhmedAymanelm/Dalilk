from pydantic import BaseModel , Field, validator
from bson.objectid import ObjectId  
from typing import Optional
from datetime import datetime



class Asset(BaseModel):
    id : Optional[ObjectId] = Field(None, alias="_id")
    asset_project_id :  ObjectId
    asset_name : str = Field(..., min_length=1)
    asset_type : str = Field(..., min_length=1)
    asset_size : int = Field(gt= 0,default=0)
    assets_config : dict = Field(default= None ) 
    asset_push_at : datetime  = Field(default=datetime.utcnow)
    



    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True

    
    @classmethod
    def get_index(cls):
        return [
            {
                "key": [("asset_project_id", 1)],
                "name": "asset_project_id_1",
                "unique": False
            },
            {
                "key": [
                    ("asset_project_id", 1),
                    ("asset_name", 1)
                        ],
                "name": "asset_project_name_id_1",
                "unique": True
            }
        ]
 