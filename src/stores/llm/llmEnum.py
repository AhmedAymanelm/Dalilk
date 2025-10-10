from enum import Enum

class LLMType(Enum):
     OPENAI = "openai"
     COhere="cohere"
     Groq="groq"

     HuggingFace="huggingface"
     Azure="azure"
     Google="google"
     Custom="custom"



class OPENAIENUM(Enum):
     SYSTEM = "system"
     USER = "user"
     ASSISTANT = "assistant"



class CohereENUM(Enum):
     SYSTEM = "SYSTEM"
     USER = "USER"
     ASSISTANT = "CHATBOT"

     DECUMENT = "search_decument"
     QURY = "search_qury"


class GROQENUM(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class DecumentTypeEnum(Enum):
     DECUMENT = "decument"
     QURY = "qury"
