from ..VectorDbInterface import VectorDbInterface
from ..VectorDbEnums import DestanceModelEnum
from qdrant_client import QdrantClient, models
from typing import List, Dict

import logging



class QdrantDBProvider(VectorDbInterface):
    def __init__(self, db_path:str, distance_model:DestanceModelEnum):
        self.client = None
        self.db_path = db_path
        self.distance_method = None
        # Accept either enum or string for distance_model
        try:
            dm_val = distance_model.value if hasattr(distance_model, 'value') else str(distance_model)
            dm_val = dm_val.strip().lower()
        except Exception:
            dm_val = str(distance_model).strip().lower()

        # tolerant mapping for common names / misspellings
        mapping = {
            'cosine': DestanceModelEnum.COSINE.value,
            'cosin': DestanceModelEnum.COSINE.value,
            'cos': DestanceModelEnum.COSINE.value,
            'dot': DestanceModelEnum.DOT.value,
            'dotproduct': DestanceModelEnum.DOT.value,
        }

        mapped = mapping.get(dm_val)
        if mapped == DestanceModelEnum.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif mapped == DestanceModelEnum.DOT.value:
            self.distance_method = models.Distance.DOT
        else:
            supported = ', '.join([e.value for e in DestanceModelEnum])
            raise Exception(f"Distance model not supported: {distance_model}. Supported: {supported}")
        
        self.logger = logging.getLogger(__name__)


    def connect(self):
        # Try to initialize QdrantClient from various db_path formats:
        # - full URL (http://... or https://...)
        # - host:port -> treated as http://host:port
        # - local path (fallback) -> try local client if available
        dp = (self.db_path or "").strip()
        if not dp:
            raise RuntimeError("VECTOR_DB_PATH is empty or not configured")

        try:
            if dp.startswith("http://") or dp.startswith("https://"):
                self.client = QdrantClient(url=dp)
                return

            # host:port -> assume http
            if ":" in dp and not dp.startswith("/"):
                self.client = QdrantClient(url=f"http://{dp}")
                return

            # Fallback: try treating as a local path (qdrant local)
            # QdrantClient in some installs supports path parameter; try that first
            try:
                self.client = QdrantClient(path=dp)
                return
            except TypeError:
                # older/newer qdrant-client may not accept path kwarg; fallback to url
                self.client = QdrantClient(url=f"http://{dp}")
                return

        except Exception as e:
            # provide more actionable error text
            self.logger.exception("Failed to create Qdrant client")
            raise RuntimeError(f"Failed to connect to Qdrant at '{self.db_path}': {e}") from e
    
    def disconnect(self):
        self.client = None

    
    def is_collection_existes(self,collection_name: str) -> bool:
       return self.client.collection_exists(collection_name=collection_name) 
         
    def list_all_collection(self, id: str) -> List:
        return self.client.get_collections()
    

    def get_collection_Info(self, collection_name: str) -> Dict:
        try:
            return self.client.get_collection(collection_name=collection_name)
        except ValueError as e:
            # qdrant local client raises ValueError when collection is not found
            self.logger.warning(f"Collection '{collection_name}' not found: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Error getting collection info for '{collection_name}': {e}")
            raise
    

    def delete_collection(self, collection_name: str):
        if self.is_collection_existes(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)
    
    def create_collection(self, collection_name: str, embidding_size:int , do_reset : bool = False) :
        if do_reset:
           _ =  self.delete_collection(collection_name=collection_name)
        
        if not self.is_collection_existes(collection_name=collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embidding_size, distance=self.distance_method)
            )
        
            return True
        
        return False
    

    def insert_one(self, collection_name: str, text: str, vector:List, metadata: Dict = None , record_id : str = None):
        if not self.is_collection_existes(collection_name):
           self.logger.error(f"Collection {collection_name} does not exist")
            
           return False
        try: 
            _ =  self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=[record_id],
                        vector=vector,
                        payload={
                            "text": text,
                            "metadata": metadata
                        },
                    )  
                        
                ]
            )
        except Exception as e:
                self.logger.error(f"Error uploading batch to collection {collection_name}: {e}")
                return False
        return True
    


    def insert_many(self, collection_name: str, texts: List, vectors: List, metadata: Dict = None, record_ids: str = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0 ,len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]
            batch_record = [
                models.Record(
                     id=batch_record_ids[x],
                     vector=batch_vectors[x],
                     payload={
                         "text": batch_texts[x],
                         "metadata": batch_metadata[x]
                     },
                 )  
                for x in range(len(batch_texts))
            ]
            try:
                _ =  self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_record
                )
            except Exception as e:
                self.logger.error(f"Error uploading batch to collection {collection_name}: {e}")
                return False

        return True
    

    def search_vectors(self, collection_name: str, vectors:list ,limit:int=4) :
        return self.client.search(
            collection_name=collection_name,
            query_vector=vectors,
            limit=limit

        )

       