from .BaseControlls import BaseControlls
from models.db_schemas import Project
from models.db_schemas.data_Chunks import DataChunk
from stores.llm.llmEnum import DecumentTypeEnum
from typing import List
import json



class  NLPController(BaseControlls):
    def __init__(self,generation_client,embedding_client,vector_db_client):
        super().__init__()

        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.vector_db_client = vector_db_client
    
    def create_collection_name(self, project_id:str):
        return f"collection_{project_id}".strip()
    
    def reset_DB_collection(self, project:Project):
        collection_name = self.create_collection_name( project_id  = project.project_id)
        return self.vector_db_client.delete_collection(collection_name=collection_name)
    


    def get_collection_info(self, project:Project):
        collection_name = self.create_collection_name( project_id  = project.project_id)
        collection_info =  self.vector_db_client.get_collection_Info(collection_name=collection_name)
        if collection_info is None:
            return None

        # collection_info may be an object returned by the client; produce a JSON-compatible dict
        if isinstance(collection_info, dict):
            return collection_info

        return json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))
    
    def index_into_vectordb(self, project:Project, chunk:List[DataChunk], 
                                   chunks_ids:List[int],
                                   do_reset:bool = False):
        

       # step 1 : get the collection name
       collection_name = self.create_collection_name( project_id = project.project_id)

       # step 2 : manage item
       texts =[c.Chunk_text  for c in chunk]
       metadata = [c.Chunk_metadata  for c in chunk]

       vectors = [
         # pass document type positionally to support providers with different kwarg names
         self.embedding_client.embed_text(text, DecumentTypeEnum.DECUMENT.value)
                                            
           for text in texts
          
       ]

       # step 3 : create collection if not exist
       _ = self.vector_db_client.create_collection(
           collection_name=collection_name,
           do_reset = do_reset,
           embidding_size = self.embedding_client.embedding_size
           
           )

       # step 4 : insert into vector db

       _ = self.vector_db_client.insert_many(
           collection_name=collection_name, 
           texts = texts,
           metadata = metadata,
           vectors = vectors, 
           record_ids = chunks_ids
           )

       return True
    

    def search_in_vectordb(self, project:Project, text:str, limit:int = 4):
        collection_name = self.create_collection_name( project_id  = project.project_id)

        vector = self.embedding_client.embed_text(text=text, dcoument_type= DecumentTypeEnum.QURY.value)

        if not vector or  len (vector) == 0:

            return False

        result =   self.vector_db_client.search_vectors(
            collection_name=collection_name,
            vectors = vector,
            limit = limit
        )
        if not result or  len (result) == 0:

            return False

        return json.loads(json.dumps(result, default=lambda x: x.__dict__))