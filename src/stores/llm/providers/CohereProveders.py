from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import CohereENUM, DecumentTypeEnum
import cohere
import logging


class CohereProvider(LLMInterfaceFactory):
    def __init__(
        self,
        api_key: str,
        api_url: str = None,
        defult_input_max_character: int = 1000,
        defult_output_max_character: int = 1000,
        defult_generation_temperature: float = 0.1,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.defult_input_max_character = defult_input_max_character
        self.defult_output_max_character = defult_output_max_character
        self.defult_generation_temperature = defult_generation_temperature

        self.generate_model_id = None
        self.emmbedding_model_id = None
        self.embedding_size = None

        # Initialize Cohere V2 client
        self.client = cohere.ClientV2(self.api_key, api_url=self.api_url) if self.api_url else cohere.ClientV2(self.api_key)

        self.enums = CohereENUM
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
            self.logger.error(" Cohere client not initialized")
            return None
        if not self.generate_model_id:
            self.logger.error(" Cohere generate model not set")
            return None

        temperature = temperature or self.defult_generation_temperature
        max_tokens = max_out_tokens or self.defult_output_max_character

        messages = []
        for msg in chat_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": self.process_text(prompt)})

        try:
            response = self.client.chat(
        model=self.generate_model_id,
        messages=messages,
 )

            if hasattr(response, "message") and hasattr(response.message, "content"):
                content_blocks = response.message.content
                if isinstance(content_blocks, list) and len(content_blocks) > 0:
                    block = content_blocks[0]
                    if hasattr(block, "text"):
                        return block.text
            return response

        except Exception as e:
            self.logger.error(f"💥 Cohere chat request failed: {e}")
            raise e


    def embed_text(self, text: str, dcoument_type: str = None):
        try:
            input_type = "search_document"
            if dcoument_type and "query" in str(dcoument_type).lower():
                input_type = "search_query"

            response = self.client.embed(
                model=self.emmbedding_model_id,
                input_type=input_type,
                texts=[self.process_text(text)],
            )

            #  Cohere V2 structure
            if hasattr(response, "embeddings") and hasattr(response.embeddings, "float_"):
                return response.embeddings.float_[0]

            elif hasattr(response, "data") and len(response.data) > 0 and hasattr(response.data[0], "embedding"):
                return response.data[0].embedding

            else:
                raise ValueError("Unknown embedding response structure")

        except Exception as e:
            self.logger.error(f"💥 Error getting embedding: {e}")
            raise e

    def embed(self, texts: list[str], model: str = None, input_type: str = None):

        embeddings = []
        for text in texts:
            emb = self.embed_text(text, dcoument_type=input_type)
            if emb:
                embeddings.append(emb)
        return embeddings


    def constract_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}
