from .BaseDataModel import BaseDataModel
from .db_schemas.data_Chunks import DataChunk
from .Enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from typing import List
from pymongo import InsertOne, UpdateOne, DeleteOne



class ChunkModel(BaseDataModel):
    def __init__(self, db_client:object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNKS_NAME.value]

    @classmethod
    async def create_instans(cls, db_client:object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance



    async def init_collection(self):
        # ensure we're using the chunks collection and create configured indexes
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNKS_NAME.value]
        indexs = DataChunk.get_index()
        for index in indexs:
            await self.collection.create_index(index["key"], name=index["name"], unique=index["unique"])



    async def chunks_create(self, chunk:DataChunk):
        result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))  
        chunk._id =  result.inserted_id
        return chunk
    

    async def get_chunk(self,chunk_id:str):
        result = await self.collection.find_one({"_id":ObjectId(chunk_id)})
        if result is None:
            return None
        return DataChunk(**result)
    
    async def insert_meny_chunk(self,chunks:List , batch_size:int=100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            operations = [InsertOne(chunk.dict(by_alias=True, exclude_unset=True )) for chunk in batch]

            await self.collection.bulk_write(operations)
        return len(chunks ) 
    
    async def delete_chunk_by_project_id(self,project_id:ObjectId):
        result = await self.collection.delete_many(
            {"Chunk_project_id":project_id}
            )
        return result.deleted_count
    
    async def get_project_chunks(self,project_id:ObjectId, page_no :int=1, page_size:int=50):
        records = await self.collection.find(
                      {"Chunk_project_id":project_id}
            ).skip((page_no - 1) * page_size).limit(page_size).to_list(length= None)
        
        return [
            DataChunk(**rec) 
            for rec in records
            ]