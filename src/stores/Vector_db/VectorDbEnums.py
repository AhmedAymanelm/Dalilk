from enum import Enum


class VectorDbEnum(Enum):
    QDRENT = "qdrant"
    FAISS = "faiss"
    ANNOY = "annoy"
    HNSW = "hnsw"
    MILVUS = "milvus"
    EMBEDED = "embedded"
    VECTOR_DB = "vector_db"
    CROMADB = "cromadb"
    EMBEDED_DB = "embedded_db"


class DestanceModelEnum(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    CHEBYSHEV = "chebyshev"
    MINKOWSKI = "minkowski"
    JACCARD = "jaccard"
    TANIMOTO = "tanimoto"
    DICE = "dice"
    ROUGHNECK = "roughneck"
    SORENSEN = "sorensen"
    HAMMING = "hamming"
    JENSEN_SHANNON = "jensen_shannon"