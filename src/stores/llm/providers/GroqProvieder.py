from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import GROQENUM
from groq import Groq
import logging 


class GroqProvider(LLMInterfaceFactory):
    def __init__(self, api_key: str, api_url: str = None,
                 defult_input_max_character: int = 1000,
                 defult_output_max_character: int = 1000,
                 defult_generation_temperature: float = 0.1):
        
        self.api_key = api_key
        self.api_url = api_url

     
        self.client = Groq(
            api_key=api_key,
            api_url=api_url)

        self.defult_input_max_character = defult_input_max_character
        self.defult_output_max_character = defult_output_max_character
        self.defult_generation_temperature = defult_generation_temperature

        self.generate_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.logger = logging.getLogger(__name__)


    def set_generation_model(self, model_id: str):
        self.generate_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size



    def process_text(self, text: str):
        return text[:self.defult_input_max_character].strip()


    def generate_text(self, prompt: str, chat_history: list = [], 
                      max_out_tokens: int = None, temperature: float = None, stream: bool = False):
        
        if not self.client:
            self.logger.error("Groq client is not initialized")
            return None

        if not self.generate_model_id:
            self.logger.error("Groq generation model is not set")
            return None

        max_out_tokens = max_out_tokens if max_out_tokens else self.defult_output_max_character
        temperature = temperature if temperature else self.defult_generation_temperature

        chat_history.append(
            self.constract_prompt(prompt=prompt, role=GROQENUM.USER.value)
        )

        if stream:
            # Streaming mode
            with self.client.chat.completions.stream(
                model=self.generate_model_id,
                messages=chat_history,
                max_tokens=max_out_tokens,
                temperature=temperature
            ) as stream_response:
                for event in stream_response:
                    if event.type == "message.delta" and event.delta.content:
                        yield event.delta.content
        else:
            # Normal (non-streaming)
            response = self.client.chat.completions.create(
                model=self.generate_model_id,
                messages=chat_history,
                max_tokens=max_out_tokens,
                temperature=temperature
            )

            if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
                self.logger.error("Groq generation request failed")
                return None

            return response.choices[0].message["content"]



    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("Groq client is not initialized")
            return None

        if not self.embedding_model_id:
            self.logger.error("Groq embedding model is not set")
            return None

        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model_id
        )

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Groq embedding request failed")
            return None

        return response.data[0].embedding



    def constract_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
