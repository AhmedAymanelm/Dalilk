from pydantic import BaseModel, Field
from typing import List, Optional



class Push_Request(BaseModel):
    do_reset :Optional[int] = 0


class Search_Reqest (BaseModel):
    text : str
    limit : Optional [int] = 5