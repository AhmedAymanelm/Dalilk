from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import CohereENUM, DecumentTypeEnum
import cohere
import logging


class CohereProvider(LLMInterfaceFactory):
    def __init__(self, api_key: str, api_url: str = None, defult_input_max_character: int = 1000,
                 defult_output_max_character: int = 1000, defult_generation_temperature: float = 0.1):
        
        self.api_key = api_key
        self.api_url = api_url
        self.defult_input_max_character = defult_input_max_character
        self.defult_output_max_character = defult_output_max_character
        self.defult_generation_temperature = defult_generation_temperature

        self.generate_model_id = None
        self.emmbedding_model_id = None
        self.embedding_size = None

        # Initialize Cohere client
        if self.api_url:
            self.client = cohere.ClientV2(self.api_key, api_url=self.api_url)
        else:
            self.client = cohere.ClientV2(self.api_key)

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generate_model_id = model_id

    def set_Emmbidding_model(self, model_id: str, embedding_size: int):
        self.emmbedding_model_id = model_id
        self.embedding_size = embedding_size

    def set_embedding_model(self, model_id: str, embedding_size: int):
        return self.set_Emmbidding_model(model_id, embedding_size)

    def process_text(self, text: str):
        return text[: self.defult_input_max_character].strip()

    def generate_text(self, prompt: str, chat_history: list = [], max_out_tokens: int = None, temperature: float = None):
        if not self.client:
            self.logger.error("Cohere client not initialized")
            return None
        if not self.generate_model_id:
            self.logger.error("Cohere generate model not set")
            return None

        temperature = temperature if temperature is not None else self.defult_generation_temperature
        max_tokens = max_out_tokens if max_out_tokens is not None else self.defult_output_max_character

        response = self.client.chat(
            model=self.generate_model_id,
            chat_history=chat_history,
            message=self.process_text(prompt),
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response

    
    def embed_text(self, text: str, dcoument_type: str = None):
        if not self.client:
            self.logger.error("Cohere client not initialized")
            return None

        if not self.emmbedding_model_id:
            self.logger.error("Cohere embedding model not set")
            return None

        payload = self.process_text(text)
        if not payload.strip():
            self.logger.error("Empty text provided for embedding")
            return None

       
        input_type = "search_document"
        if dcoument_type and "qur" in str(dcoument_type).lower():
            input_type = "search_query"

        response = None
        try:
           
            response = self.client.embeddings.create(
                model=self.emmbedding_model_id,
                texts=[payload],
                input_type=input_type
            )
        except Exception as e:
            try:
            
                response = self.client.embed(
                    model=self.emmbedding_model_id,
                    texts=[payload],
                    input_type=input_type
                )
            except Exception as e2:
                self.logger.error(f"Cohere embedding request failed: {e2}")
                return None
        def extract_embedding(obj):
            if obj is None:
                return None

            
            if hasattr(obj, "embeddings"):
                emb = getattr(obj, "embeddings")
                if isinstance(emb, list) and len(emb) > 0:
                    item = emb[0]
                    if hasattr(item, "embedding"):
                        return list(item.embedding)
                    if isinstance(item, dict) and "embedding" in item:
                        return list(item["embedding"])
                    if isinstance(item, (list, tuple)):
                        return list(item)
                elif isinstance(emb, dict) and "embedding" in emb:
                    return list(emb["embedding"])
                elif isinstance(emb, (list, tuple)) and all(isinstance(x, (float, int)) for x in emb):
                    return list(emb)

           
            if hasattr(obj, "data"):
                data = getattr(obj, "data")
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    if hasattr(item, "embedding"):
                        return list(item.embedding)
                    if isinstance(item, dict) and "embedding" in item:
                        return list(item["embedding"])

     
            if isinstance(obj, dict):
                if "embeddings" in obj and isinstance(obj["embeddings"], list):
                    emb = obj["embeddings"][0]
                    if isinstance(emb, dict) and "embedding" in emb:
                        return list(emb["embedding"])
                    if isinstance(emb, (list, tuple)):
                        return list(emb)
                if "data" in obj and isinstance(obj["data"], list):
                    item = obj["data"][0]
                    if isinstance(item, dict) and "embedding" in item:
                        return list(item["embedding"])

        
            if hasattr(obj, "embedding"):
                return list(getattr(obj, "embedding"))

            return None

        emb = extract_embedding(response)
        if emb:
            self.logger.info(f"✅ Cohere embedding generated successfully (len={len(emb)})")
            return emb

        try:
            self.logger.warning(f"⚠️ Cohere unknown response structure: {response}")
        except Exception:
            pass

        return None

    def constract_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}
