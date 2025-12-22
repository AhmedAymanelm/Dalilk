from .BaseControlls import BaseControlls
from models.db_schemas import Project
from models.db_schemas.data_Chunks import DataChunk
from stores.llm.llmEnum import DecumentTypeEnum
from stores.reranker import SimpleReranker
from typing import List, Dict
import traceback
import json
from bson import ObjectId
import uuid
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class NLPController(BaseControlls):
    def __init__(self, generation_client, embedding_client, vector_db_client, template_parser):
        super().__init__()
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.vector_db_client = vector_db_client
        self.template_parser = template_parser
        self.reranker = SimpleReranker()  # Initialize reranker
        
        # Dictionary to store chat history for each session/user
        self.sessions: Dict[str, InMemoryChatMessageHistory] = {}

    def get_or_create_memory(self, session_id: str, max_token_limit: int = 2000) -> InMemoryChatMessageHistory:
        if session_id not in self.sessions:
            self.sessions[session_id] = InMemoryChatMessageHistory()
        return self.sessions[session_id]

    def clear_session_memory(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].clear()

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    def get_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vector_db_client.get_collection_Info(collection_name=collection_name)
        if collection_info is None:
            return None
        if isinstance(collection_info, dict):
            return collection_info
        return json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))
    
    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def get_embeddings(self, texts: List[str]):
        try:
            response = self.embedding_client.embed(
                texts=texts,
                model="embed-multilingual-v3.0",
                input_type="search_document",
            )
            return response
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            traceback.print_exc()
            raise

    def get_query_embedding(self, query: str):
        try:
            embedding = self.embedding_client.embed_text(
                text=query,
                dcoument_type="query",
            )
            if embedding is None:
                raise ValueError("Failed to extract embedding from embedding client")
            return embedding
        except Exception as e:
            print(f"Error getting query embedding: {str(e)}")
            raise

    def search_in_vectordb(self, project_id: str, message: str, top_k: int = 5):
        """
        Search in vector DB and rerank the results using SimpleReranker
        """
        try:
            # 1️⃣ الحصول على embedding للسؤال
            query_vector = self.get_query_embedding(message)
            collection_name = self.create_collection_name(project_id=project_id)

            # 2️⃣ البحث في قاعدة البيانات
            initial_results = self.vector_db_client.search_vectors(
                collection_name=collection_name,
                vector=query_vector,
                limit=top_k * 4,  # Get extra for reranking
            )

            # 3️⃣ تمرير النتائج على reranker
            if initial_results and len(initial_results) > 0:
                reranked_results = self.reranker.rerank(
                    results=initial_results,
                    query=message,
                    top_k=top_k
                )
                return reranked_results

            return initial_results

        except Exception as e:
            print(f"Error searching: {str(e)}")
            traceback.print_exc()
            raise
    
    def index_into_vectordb(
     
        self,
        project,
        chunks_list: List[DataChunk],
        do_reset: bool = False,
    ) -> bool:
        import traceback

        try:
            collection_name = self.create_collection_name(project_id=project.project_id)

            if do_reset:
                self.vector_db_client.delete_collection(collection_name)

            texts = [c.Chunk_text for c in chunks_list if c.Chunk_text]
            if not texts:
                return True

            # embeddings
            vectors = self.get_embeddings(texts)

            metadatas = [
                {
                    "project_id": str(project.project_id),
                    "chunk_id": str(c.id),
                    "page": getattr(c, "Chunk_page", None),
                    "source": getattr(c, "Chunk_source", None),
                }
                for c in chunks_list
            ]

            # خلي Qdrant يولد UUIDs تلقائيًا
            record_ids = None

            # إنشاء collection لو مش موجودة
            self.vector_db_client.create_collection(
                collection_name=collection_name,
                embidding_size=len(vectors[0]),
                do_reset=False,
            )

            # إدخال البيانات
            self.vector_db_client.insert_many(
                collection_name=collection_name,
                texts=texts,
                vectors=vectors,
                metadata=metadatas,
                record_ids=record_ids,
            )

            return True

        except Exception as e:
            print("❌ push_chunks_to_vectordb failed:", str(e))
            traceback.print_exc()
            return False



    def Anser_Rag_question(self, project_id: str, message: str, session_id: str = None, top_k: int = 5):
   
        answer, full_prompt = None, None

        if session_id is None:
            session_id = project_id

        memory = self.get_or_create_memory(session_id)
        chat_history_messages = memory.messages

        try:
            should_search = self.should_search_database(message, chat_history_messages)

            retrived_document = []
            database_prompt = ""

            if should_search:
                # البحث في الـ vector DB وتمرير النتائج للـ reranker
                retrived_document = self.search_in_vectordb(
                    project_id=project_id,
                    message=message,
                    top_k=top_k,
                )

                if retrived_document and len(retrived_document) > 0:
                    # بناء النص من نتائج الـ database
                    database_prompt = "\n".join(
                        [
                            self.template_parser.get(
                                "Rag",
                                "database_prompt",
                                {"db_num": idx + 1, "chunk_text": db.text},
                            )
                            for idx, db in enumerate(retrived_document)
                        ]
                    )

            system_prompt = self.template_parser.get("Rag", "system_prompt")
            footer_prompt = self.template_parser.get("Rag", "footer_prompt")

            user_question_section = f"\n\n## سؤال المستخدم:\n{message}\n"

            # تحويل الـ chat history لهيئة مناسبة للـ LLM
            chat_history = []
            chat_history.append({"role": "system", "content": system_prompt})
            for msg in chat_history_messages:
                if isinstance(msg, HumanMessage):
                    chat_history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    chat_history.append({"role": "assistant", "content": msg.content})

            full_prompt = "\n".join(
                [
                    database_prompt,
                    user_question_section,
                    footer_prompt,
                ]
            )

            # توليد الإجابة عبر الـ LLM
            answer = self.generation_client.generate_text(
                prompt=full_prompt,
                chat_history=chat_history,
            )

            # حفظ السؤال والإجابة في الـ chat history
            if answer:
                memory.add_user_message(message)
                memory.add_ai_message(answer)

        except Exception as e:
            print(f"Error in Anser_Rag_question: {str(e)}")
            traceback.print_exc()
            answer = None
            retrived_document = []

        return answer, full_prompt, self._memory_to_dict(memory), retrived_document

    def should_search_database(self, message: str, chat_history: list) -> bool:
        message_lower = message.lower()

        greetings = ['مرحبا', 'السلام', 'أهلا', 'هاي', 'عايز عربية', 'محتاج عربية', 'ساعدني']
        if any(g in message_lower for g in greetings) and len(chat_history) < 2:
            return False

        if len(message.split()) <= 2 and len(chat_history) > 0:
            return False

        has_criteria = any([
            any(price_word in message_lower for price_word in ['ألف', '000', 'جنيه', 'egp']),
            any(fuel in message_lower for fuel in ['كهربا', 'بنزين', 'ديزل', 'electric', 'petrol']),
            any(body in message_lower for body in ['sedan', 'suv', 'سيدان', 'هاتشباك']),
            any(brand in message_lower for brand in ['mg', 'byd', 'chery', 'jeep', 'geely']),
            'مواصفات' in message_lower or 'سعر' in message_lower,
        ])

        if not has_criteria and len(chat_history) >= 4:
            return True

        return has_criteria

    def _memory_to_dict(self, memory: InMemoryChatMessageHistory) -> list:
        chat_history = []
        for msg in memory.messages:
            if isinstance(msg, HumanMessage):
                chat_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                chat_history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                chat_history.append({"role": "system", "content": msg.content})
        return chat_history
