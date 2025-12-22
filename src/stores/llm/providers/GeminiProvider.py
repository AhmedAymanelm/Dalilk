from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import GINIEnum
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

class GeminiProvider(LLMInterfaceFactory):
    def __init__(
        self,
        api_key: str,  
        api_url: str = None,  
        defult_input_max_character: int = 1000,  
        defult_output_max_character: int = 1000,  
        defult_generation_temperature: float = 0, 
        
    ):
        self.api_key = api_key  
        self.api_url = api_url 
        self.defult_input_max_character = defult_input_max_character  
        self.defult_output_max_character = defult_output_max_character  
        self.defult_generation_temperature = defult_generation_temperature  

        self.generate_model_id = None
        self.emmbedding_model_id = None  
        self.embedding_size = None  

        # Don't instantiate a client here because `ChatGoogleGenerativeAI` requires
        # a `model` field at construction time. We create a client per-call in
        # `generate_text` where `self.generate_model_id` is guaranteed to be set.
        self.client = None

        self.enums = GINIEnum
        self.logger = logging.getLogger(__name__)


    def set_generation_model(self, model_id: str):
        self.generate_model_id = model_id

    def set_Emmbidding_model(self, model_id: str, embedding_size: int):
        self.emmbedding_model_id = model_id
        self.embedding_size = embedding_size
    
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.emmbedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text

    def generate_text(self, prompt: str, chat_history: list = [], max_out_tokens: int = None, temperature: float = None):
        if self.generate_model_id is None:
            raise ValueError("Generate model id is not set")

        if max_out_tokens is None:
            max_out_tokens = self.defult_output_max_character

        if temperature is None:
            temperature = self.defult_generation_temperature

        # Ensure temperature is a valid float
        if not isinstance(temperature, (int, float)):
            temperature = 0.1

        # Create a new client instance with current parameters
        client = ChatGoogleGenerativeAI(
            model=self.generate_model_id,
            api_key=self.api_key,
            temperature=float(temperature),
            max_output_tokens=max_out_tokens
        )

        # Convert chat_history to messages format
        messages = []
        for msg in chat_history:
            if msg["role"] == "system":
                messages.append(("system", msg["content"]))
            elif msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("ai", msg["content"]))

        # Add current prompt
        messages.append(("human", prompt))

        try:
            response = client.invoke(messages)
            return response.content
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            raise
    

    def embed_text(self, text: str, dcoument_type: str = None):
        try:
            if not self.emmbedding_model_id:
                raise ValueError(" Embedding model not set for Gemini")

            raise NotImplementedError("Gemini does not support embeddings. Use OpenAI or Cohere instead.")

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
                self.logger.warning("⚠️ Embeddings not supported by Gemini")
                break
        return embeddings

    def constract_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}