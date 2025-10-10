from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMInterfaceFactory(ABC):
     
    @abstractmethod
    def set_generation_model (self, model_name:str):
        pass

    @abstractmethod
    def set_Emmbidding_model(self, model_name:str,embedding_size:int):
        pass

    @abstractmethod
    def generate_text(self, prompt:str, chat_history:list=[], max_out_tokens:int = None, temperature:float = None):

        pass

    @abstractmethod
    def embed_text(self, text:str, dcoument_type:str = None):
        pass

    @abstractmethod
    def constract_prompt(self, prompt:str, role:str):
        pass