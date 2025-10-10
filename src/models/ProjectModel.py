from .BaseDataModel import BaseDataModel
from .db_schemas.Project import ProjectBase
from .Enums.DataBaseEnum import DataBaseEnum
from motor.motor_asyncio import AsyncIOMotorClient



class ProjectModels(BaseDataModel):
    def __init__(self, db_client:object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    @classmethod
    async def create_instans(cls, db_client:object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    
    async def init_collection(self):
          all_collection = await self.db_client.list_collection_names()
          if DataBaseEnum.COLLECTION_PROJECT_NAME.value not in all_collection:
             self.collection  = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
             indexs = ProjectBase.get_index() 
             for index in indexs:
                 await self.collection.create_index(
                     index["key"],
                     name=index["name"],
                     unique=index["unique"],
                     
                     )


    async def create_project(self, project:ProjectBase):
        result =  await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        return project
    

    async def get_project_or_create_one(self, project_id:str):
        record = await self.collection.find_one({
            "project_id" : project_id
            })
        
        if record is None:
            project = ProjectBase(project_id=project_id)
            project = await self.create_project(project)
            return project
    
        return ProjectBase(**record)
        
    
    async def get_all_project(self, page_size:int=10, page:int=1):
        total_doucments = await self.collection.find().count_documents({})
        total_pages = total_doucments // page_size
        if total_doucments % page_size > 0:
            total_pages += 1
        cursor =  await self.collection.find().skip((page-1)* page_size).limit(page_size)
        projects = []
        async for doc in cursor:
            projects.append(ProjectBase(**doc))
        return projects, total_pages




    