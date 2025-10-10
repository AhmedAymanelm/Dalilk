from .BaseDataModel import BaseDataModel
from .db_schemas.Project import ProjectBase
from .Enums.DataBaseEnum import DataBaseEnum
from .db_schemas import Asset
from bson import ObjectId

class AssetModel(BaseDataModel):
        def __init__(self, db_client:object):
            super().__init__(db_client=db_client)
            self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSETS_NAME.value]


        @classmethod
        async def create_instans_Assets(cls, db_client:object):
                instance = cls(db_client)
                await instance.init_collection()
                return instance



        async def init_collection(self):
            # ensure we're using the assets collection and create the configured indexes
            self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSETS_NAME.value]
            indexs = Asset.get_index()
            for index in indexs:
                # create_index is idempotent — it's safe to call even if the index exists
                await self.collection.create_index(index["key"], name=index["name"], unique=index["unique"])
                 
        async def create_asset(self, asset:Asset):
            result =  await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))
            asset.id = result.inserted_id
            return asset
        
        async def get_all_asset(self, asset_project_id: str, asset_type: str):
            # query the collection for assets matching project id and type
            query = {
                "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
                "asset_type": asset_type,
            }
            cursor =  await self.collection.find(query).to_list(length=None)
            return [
                 Asset(**doc) for doc in cursor

            ]
        
        async def get_asset_record(self, asset_project_id: str, asset_name: str):
            # find a single asset by project id and asset_name
            query = {
                "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
                "asset_name": asset_name,
            }
            record = await self.collection.find_one(query)
            if record:
                return Asset(**record)
            return None
            

