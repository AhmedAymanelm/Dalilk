from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorDbInterface(ABC):



    @abstractmethod
    def connect(self):
        pass


    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_collection_existes(self,collection_name: str) -> bool:
        pass

    @abstractmethod
    def list_all_collection(self, id: str) -> List:
        pass

    @abstractmethod
    def get_collection_Info(self, collection_name: str) -> Dict:

        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, embidding_size:int , do_reset : bool = False) :
        pass

    
    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector:List, metadata: Dict = None , record_id : str = None):
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: List, vectors: List, metadata: Dict = None, record_ids: str = None, batch_size: int = 50):
        pass

    @abstractmethod
    def search_vectors(self, collection_name: str, vectors:list ,limit:int) :
        pass
    