from ..VectorDbInterface import VectorDbInterface
from ..VectorDbEnums import DestanceModelEnum
from qdrant_client import QdrantClient, models
from typing import List, Dict
from models.db_schemas import RetrevedDecument
import logging
import uuid


class QdrantDBProvider(VectorDbInterface):

    def __init__(self, db_path: str, distance_model: DestanceModelEnum):
        self.client = None
        self.db_path = db_path
        self.distance_method = None

        # Normalize distance model
        dm_val = (
            distance_model.value
            if hasattr(distance_model, "value")
            else str(distance_model)
        ).strip().lower()

        mapping = {
            "cosine": DestanceModelEnum.COSINE.value,
            "cosin": DestanceModelEnum.COSINE.value,
            "cos": DestanceModelEnum.COSINE.value,
            "dot": DestanceModelEnum.DOT.value,
            "dotproduct": DestanceModelEnum.DOT.value,
        }

        mapped = mapping.get(dm_val)
        if mapped == DestanceModelEnum.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif mapped == DestanceModelEnum.DOT.value:
            self.distance_method = models.Distance.DOT
        else:
            supported = ", ".join([e.value for e in DestanceModelEnum])
            raise ValueError(
                f"Distance model not supported: {distance_model}. Supported: {supported}"
            )

        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self):
        dp = (self.db_path or "").strip()
        if not dp:
            raise RuntimeError("VECTOR_DB_PATH is empty or not configured")

        try:
            if dp.startswith("http://") or dp.startswith("https://"):
                self.client = QdrantClient(url=dp)
                return

            if ":" in dp and not dp.startswith("/"):
                self.client = QdrantClient(url=f"http://{dp}")
                return

            try:
                self.client = QdrantClient(path=dp)
                return
            except TypeError:
                self.client = QdrantClient(url=f"http://{dp}")
                return

        except Exception as e:
            self.logger.exception("Failed to create Qdrant client")
            raise RuntimeError(f"Failed to connect to Qdrant at '{dp}': {e}") from e

    def disconnect(self):
        self.client = None

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------
    def is_collection_existes(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collection(self):
        return self.client.get_collections()

    def get_collection_Info(self, collection_name: str):
        try:
            return self.client.get_collection(collection_name=collection_name)
        except Exception:
            return None

    def delete_collection(self, collection_name: str):
        if self.is_collection_existes(collection_name):
            self.client.delete_collection(collection_name=collection_name)

    def create_collection(
        self,
        collection_name: str,
        embidding_size: int,
        do_reset: bool = False,
    ):
        if do_reset:
            self.delete_collection(collection_name)

        if not self.is_collection_existes(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embidding_size,
                    distance=self.distance_method,
                ),
                # استخدم dict مباشر لتفادي مشاكل OptimizersConfig القديمة
                optimizers_config={
                    "indexing_threshold": 0
                },
                # HNSWConfig كامل مع كل الحقول المطلوبة
                hnsw_config=models.HnswConfig(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10000 
                ),
            )
            return True

        return False



    def force_reindex(self, collection_name: str):
        self.client.update_collection(
            collection_name=collection_name,
            optimizers_config={
                "indexing_threshold": 0
            },
            hnsw_config={
                "m": 16,
                "ef_construct": 100,
                "full_scan_threshold": 10000
            }
       )

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------
    def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: List[float],
        metadata: Dict = None,
        record_id: str = None,
    ):
        self.client.upload_records(
            collection_name=collection_name,
            records=[
                models.Record(
                    id=record_id,
                    vector=vector,
                    payload={
                        "text": text,
                        "metadata": metadata or {},
                    },
                )
            ],
        )
        return True

    def insert_many(
        self,
        collection_name: str,
        texts: List[str],
        vectors: List[List[float]],
        metadata: List[Dict] = None,
        record_ids: List = None,
        batch_size: int = 64,
    ):
        

        if metadata is None:
            metadata = [{} for _ in texts]

        if record_ids is None:
            record_ids = [str(uuid.uuid4()) for _ in texts]

        for i in range(0, len(texts), batch_size):
            batch = [
                models.Record(
                    id=record_ids[i + j],
                    vector=vectors[i + j],
                    payload={
                        "text": texts[i + j],
                        "metadata": metadata[i + j],
                    },
                )
                for j in range(min(batch_size, len(texts) - i))
            ]

            self.client.upload_records(
                collection_name=collection_name,
                records=batch,
            )

        return True


    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_vectors(
        self,
        collection_name: str,
        vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.25,
    ):
        results = self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
        )

        if not results:
            return []

        return [
            RetrevedDecument(
                text=r.payload.get("text", ""),
                score=r.score,
            )
            for r in results
        ]
