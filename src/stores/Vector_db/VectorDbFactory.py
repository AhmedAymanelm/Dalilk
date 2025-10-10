from .Providers import QdrantDBProvider
from .VectorDbEnums import VectorDbEnum
from controlles import BaseControlls


class VectorDbFactory:
    def __init__(self, config ):
        self.config = config
        self.base_controlls = BaseControlls()


    def create(self, provider: str):
        if not provider:
            raise ValueError("VECTOR_DB provider is not configured. Set settings.VECTOR_DB_BACKEND to one of: " + ", ".join([e.value for e in VectorDbEnum]))

        name = provider.lower()
        if name == VectorDbEnum.QDRENT.value:
            db_path = self.base_controlls.get_database_path(db_name=self.config.VECTOR_DB_PATH)
            return QdrantDBProvider(
                db_path=db_path,
                distance_model=self.config.VECTOR_DB_DESTANCE,
            )

        raise ValueError(f"Unsupported VECTOR_DB provider '{provider}'. Supported: " + ", ".join([e.value for e in VectorDbEnum]))

