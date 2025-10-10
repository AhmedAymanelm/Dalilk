from pydantic import BaseModel, Field
from typing import List, Optional



class ProcessReqest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap: Optional[int] = 20
    do_reset: Optional[bool] = 0
