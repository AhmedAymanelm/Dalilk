from ..LLMinterfacefactory import LLMInterfaceFactory
from ..llmEnum import HuggingFaceENUM
import logging
from typing import List
import torch
import os


os.environ.setdefault("TRANSFORMERS_NO_TF", "1")


class HuggingFaceProvider(LLMInterfaceFactory):
    def __init__(
        self,
        api_key: str = None,
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
        self.embedding_model = None  # SentenceTransformer model

        self.enums = HuggingFaceENUM
        self.logger = logging.getLogger(__name__)
        
        # تحديد الجهاز (GPU أو CPU)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.logger.info(f"🔧 Using device: {self.device}")


    def set_generation_model(self, model_id: str):
        """
        حالياً Hugging Face للـ generation غير مدعوم في هذا الكود
        يمكنك استخدام Groq أو OpenAI للـ generation
        """
        self.generate_model_id = model_id
        self.logger.warning("⚠️ Hugging Face generation not implemented. Use Groq/OpenAI for generation.")

    def set_Emmbidding_model(self, model_id: str, embedding_size: int):
        """تحميل نموذج Embeddings من Hugging Face"""
        self.emmbedding_model_id = model_id
        self.embedding_size = embedding_size
        
        try:
            # Lazy import لتجنب تحميل TensorFlow
            from sentence_transformers import SentenceTransformer
            
            self.logger.info(f"📥 Loading Hugging Face model: {model_id}")
            self.embedding_model = SentenceTransformer(model_id, device=self.device)
            self.logger.info(f"✅ Model loaded successfully on {self.device}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load model {model_id}: {e}")
            raise

    def set_embedding_model(self, model_id: str, embedding_size: int):
        return self.set_Emmbidding_model(model_id, embedding_size)

    def process_text(self, text: str):
        return text[: self.defult_input_max_character].strip()

    def generate_text(self, prompt: str, chat_history: list = [], max_out_tokens: int = None, temperature: float = None):
        """
        ⚠️ Generation غير مدعوم
        استخدم Groq أو OpenAI للـ generation
        """
        self.logger.error("❌ Hugging Face generation not implemented")
        raise NotImplementedError("Use Groq or OpenAI for text generation")

    def embed_text(self, text: str, dcoument_type: str = None):
        """
        تحويل نص واحد إلى embedding باستخدام Hugging Face
        """
        if not self.embedding_model:
            raise ValueError("❌ Embedding model not loaded. Call set_embedding_model() first.")
        
        try:
            processed_text = self.process_text(text)
            # تحويل النص إلى embedding
            embedding = self.embedding_model.encode(
                processed_text,
                convert_to_tensor=False,  # نرجع numpy array
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"❌ Error generating embedding: {e}")
            raise

    def embed(self, texts: List[str], model: str = None, input_type: str = None):
        """
        تحويل عدة نصوص إلى embeddings دفعة واحدة (أسرع)
        """
        if not self.embedding_model:
            raise ValueError("❌ Embedding model not loaded. Call set_embedding_model() first.")
        
        try:
            # معالجة النصوص
            processed_texts = [self.process_text(text) for text in texts]
            
            # تحويل دفعة واحدة (أسرع من واحد واحد)
            embeddings = self.embedding_model.encode(
                processed_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
                batch_size=32  # يمكنك تعديل حجم الـ batch
            )
            
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            self.logger.error(f"❌ Error generating embeddings: {e}")
            raise

    def constract_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}
