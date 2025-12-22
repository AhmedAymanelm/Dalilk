from pydantic import BaseModel, Field
from typing import List, Optional, Dict



class Push_Request(BaseModel):
    do_reset :Optional[int] = 0


class Search_Reqest (BaseModel):
    message : str = Field(..., alias='query')  # يقبل message أو query
    limit : Optional [int] = 5
    session_id: Optional[str] = None  # معرف الجلسة للمستخدم
    
    class Config:
        populate_by_name = True  # يسمح باستخدام message أو query