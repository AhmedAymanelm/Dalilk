from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import GROQENUM
from groq import Groq
import logging


class GroqProviders(LLMInterfaceFactory):
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

        # Initialize Groq client
        self.client = Groq(api_key=self.api_key, base_url=self.api_url) if self.api_url else Groq(api_key=self.api_key)

        self.enums = GROQENUM
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
            self.logger.error(" Groq client not initialized")
            return None
        if not self.generate_model_id:
            self.logger.error(" Groq generate model not set")
            return None

        temperature = temperature or self.defult_generation_temperature
        max_tokens = max_out_tokens or self.defult_output_max_character

        messages = []
        for msg in chat_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": self.process_text(prompt)})

        try:
            response = self.client.chat.completions.create(
                model=self.generate_model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return choice.message.content
            return response

        except Exception as e:
            self.logger.error(f"💥 Groq chat request failed: {e}")
            raise e

    def embed_text(self, text: str, dcoument_type: str = None):
        """
        ⚠️ Groq لا يدعم Embeddings حالياً
        يمكنك استخدام OpenAI أو Cohere للـ Embeddings
        """
        try:
            if not self.emmbedding_model_id:
                raise ValueError(" Embedding model not set for Groq")

            raise NotImplementedError("Groq does not support embeddings. Use OpenAI or Cohere instead.")

        except Exception as e:
            self.logger.error(f" Error getting embedding: {e}")
            raise e

    def embed(self, texts: list[str], model: str = None, input_type: str = None):
  
        embeddings = []
        for text in texts:
            try:
                emb = self.embed_text(text, dcoument_type=input_type)
                if emb:
                    embeddings.append(emb)
            except NotImplementedError:
                self.logger.warning("⚠️ Embeddings not supported by Groq")
                break
        return embeddings
    
    def constract_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}