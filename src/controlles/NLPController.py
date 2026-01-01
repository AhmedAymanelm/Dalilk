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
            
            query_vector = self.get_query_embedding(message)
            collection_name = self.create_collection_name(project_id=project_id)

            
            initial_results = self.vector_db_client.search_vectors(
                collection_name=collection_name,
                vector=query_vector,
                limit=top_k * 4,  
            )

            
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

            
            record_ids = None

            
            self.vector_db_client.create_collection(
                collection_name=collection_name,
                embidding_size=len(vectors[0]),
                do_reset=False,
            )

           
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
        
        print(f"\n💬 [MEMORY DEBUG]")
        print(f"   Session ID: {session_id}")
        print(f"   Memory messages count: {len(chat_history_messages)}")
        for idx, msg in enumerate(chat_history_messages):
            msg_type = "User" if isinstance(msg, HumanMessage) else "Assistant"
            msg_preview = msg.content[:80] if len(msg.content) > 80 else msg.content
            print(f"   [{idx}] {msg_type}: {msg_preview}")

        try:
            # ✅ Simple logic: Show cars after proper discussion
            # Ask 2-3 questions to understand user needs before showing cars
            retrived_document = []
            database_prompt = ""
            
            # 🔥 NO STATIC DETECTION - Let LLM handle everything!
            # LLM is smart enough to understand greetings, off-topic, follow-ups, etc.
            
            message_lower = message.lower()
            
            # Check if user gave car criteria
            has_budget = any(x in message_lower for x in ['ألف', 'الف', 'مليون', 'جنيه', '000'])
            has_brand = any(x in message_lower for x in [
                'mg', 'byd', 'تويوتا', 'هيونداي', 'مرسيدس', 'بي ام',
                'بورش', 'porsche', 'فيراري', 'ferrari', 'لامبورجيني', 'lamborghini',
                'بنتلي', 'bentley', 'رولز', 'rolls', 'اودي', 'audi',
                'نيسان', 'nissan', 'كيا', 'kia', 'فورد', 'ford',
                'جينيسيس', 'genesis', 'كوبرا', 'cupra',
                'بيجو', 'peugeot', 'شيري', 'chery', 'جيلى', 'جيلي', 'geely',
                'سوزوكي', 'suzuki', 'ميتسوبيشي', 'mitsubishi', 'سكودا', 'skoda',
                'سوبارو', 'subaru', 'هوندا', 'honda', 'مازدا', 'mazda',
                'سيتروين', 'citroen', 'رينو', 'renault', 'جيب', 'jeep', 
                'اوبل', 'opel', 'ام جى', 'ام جي',
            ])
            has_type = any(x in message_lower for x in ['sedan', 'suv', 'سيدان', 'هاتشباك'])
            has_usage = any(x in message_lower for x in ['شغل', 'سفر', 'عائلي', 'شخصي'])
            
            # Count criteria
            criteria_count = sum([has_budget, has_brand, has_type, has_usage])
            
            # 🔥 Need at least 3 criteria OR 6+ messages (3 Q&A rounds)
            user_gave_criteria = has_budget or has_brand or has_type or has_usage
            has_enough_criteria = criteria_count >= 3 or has_brand  # Brand alone is enough
            conversation_has_enough_info = len(chat_history_messages) >= 6 or has_enough_criteria
            
            print(f"\n🔍 [SEARCH DECISION]")
            print(f"   Chat history messages: {len(chat_history_messages)}")
            print(f"   User gave criteria: {user_gave_criteria} (budget={has_budget}, brand={has_brand}, type={has_type}, usage={has_usage})")
            print(f"   Criteria count: {criteria_count}")
            print(f"   Has enough info: {conversation_has_enough_info}")
            
            # Always search if user gave criteria or conversation progressed
            if conversation_has_enough_info:
                print(f"Sending cars to LLM")
                
                # 🔍 Smart Top-K Adjustment
                import re
                
                # Known brands normalized
                brands = [
                    'mg', 'byd', 'تويوتا', 'هيونداي', 'مرسيدس', 'بي ام',
                    'بورش', 'porsche', 'فيراري', 'ferrari', 'لامبورجيني', 'lamborghini',
                    'بنتلي', 'bentley', 'رولز', 'rolls', 'اودي', 'audi',
                    'نيسان', 'nissan', 'كيا', 'kia', 'فورد', 'ford',
                    'سيتروين', 'citroen', 'رينو', 'renault', 'جيب', 'jeep', 
                    'اوبل', 'opel', 'بيجو', 'peugeot', 'شيري', 'chery', 'جيلى', 'geely',
                    'سوزوكى', 'suzuki', 'ميتسوبيشي', 'mitsubishi', 'سكودا', 'skoda',
                    'سوبارو', 'subaru', 'هوندا', 'honda', 'مازدا', 'mazda',
                    'جينيسيس', 'genesis', 'كوبرا', 'cupra',
                ]
                
                ignored_tokens = [
                    'sedan', 'suv', 'hatchback', 'coupe', 'crossover', 'fob', 
                    'automatic', 'manual', 
                    'new', 'used', 'best', 'price', 'cost', 'buy', 'want', 'need', 'show',
                    'details', 'info', 'information', 'about', 'car', 'cars', 'vehicle',
                    'good', 'bad', 'review', 'opinion', 'vs', 'compare',
                    'سيدان', 'هاتشباك', 'اس', 'يو', 'في', 'اوتوماتيك', 'مانيوال',
                    'جديد', 'مستعمل', 'سعر', 'اسعار', 'بكام', 'بكم',
                    'عربية', 'عربيات', 'سيارة', 'سيارات',
                    'تفاصيل', 'معلومات', 'صور', 'شكل',
                    'رايك', 'ايه', 'احسن', 'افضل'
                ]
                
                # Check for "extra" specific tokens that are NOT the brand and NOT ignored
                tokens = re.findall(r'[a-zA-Z0-9\u0600-\u06FF]+', message_lower)
                
                def is_specific_token(t):
                    if t.isdigit(): return False # Ignore pure numbers (often years or prices)
                    if t in brands: return False
                    if t in ignored_tokens: return False
                    if len(t) < 2: return False
                    return True

                specific_tokens = [t for t in tokens if is_specific_token(t)]
                
                has_specific_model_hint = has_brand and len(specific_tokens) > 0
                
                # 🔥 Fix: Increase defaults. Even for specific models, show variations (e.g. different years/trims)
                dynamic_top_k = 3 if has_specific_model_hint else 10
                
                # Respect the requested top_k from parameter if provided and larger
                if top_k and top_k > dynamic_top_k:
                    dynamic_top_k = top_k

                print(f"   🎯 Search strategy: {'Specific Car' if has_specific_model_hint else 'Broad Search'} -> top_k={dynamic_top_k}")

                
                # If message is just "show me" or "tell me details", get car name from AI's previous response
                search_query = message
                clean_msg_tokens = [t for t in tokens if t not in ignored_tokens]
                
                # 🔥 Check for "show me" type queries
                show_keywords = ['وريني', 'ورني', 'عايز اشوف', 'عايز أشوف', 'التفاصيل', 'مواصفات', 'اعرض', 'شوفني', 'show', 'details']
                is_show_request = any(k in message_lower for k in show_keywords)
                
                # If current message has NO specific content (brands, numbers, or non-ignored words)
                # OR if it's a "show me" request
                if (not has_brand and not has_budget and len(clean_msg_tokens) == 0) or is_show_request:
                    print(f"   ⚠️ Generic/show query detected '{message}' - Looking back in history for car names...")
                    
                    found_context = False
                    # Look back in messages - check BOTH user and AI messages for car names
                    for past_msg in reversed(chat_history_messages[-6:]):  # Look at last 6 messages (3 exchanges)
                        content_lower = past_msg.content.lower() if past_msg.content else ""
                        
                        # 🔥 For AI messages: Extract car names mentioned
                        if isinstance(past_msg, AIMessage):
                            # Look for brand names in AI's response
                            for brand in brands:
                                if brand in content_lower:
                                    # Extract the sentence containing the brand
                                    import re
                                    brand_patterns = [
                                        rf'{brand}\s+[\u0600-\u06FF\w]+\s*\d*',
                                        rf'{brand}',
                                    ]
                                    for pattern in brand_patterns:
                                        match = re.search(pattern, content_lower)
                                        if match:
                                            car_name = match.group(0)
                                            search_query = car_name
                                            print(f"   ✅ Found car in AI response: '{car_name}'")
                                            found_context = True
                                            break
                                    if found_context:
                                        break
                            if found_context:
                                break
                        
                        # 🔥 For User messages: Check if they mentioned a brand
                        elif isinstance(past_msg, HumanMessage):
                            past_has_brand = any(b in content_lower for b in brands)
                            past_has_budget = any(b in content_lower for b in ['ألف', 'الف', 'مليون', 'جنيه'])
                            if past_has_brand or past_has_budget:
                                search_query = f"{past_msg.content} {message}"
                                print(f"   ✅ Appended context from user history: '{past_msg.content}'")
                                found_context = True
                                break
                    
                    if not found_context:
                        print(f" ⚠️ No car context found in history")
                
                print(f" 🚀 Final Search Query: {search_query}")

                retrived_document = self.search_in_vectordb(
                    project_id=project_id,
                    message=search_query,
                    top_k=dynamic_top_k,
                )
            else:
                print(f"   ⏭️  Skipping search - need more info from user")



            # Simply send all results to LLM - let it decide!
            if retrived_document and len(retrived_document) > 0:
                database_results = "\n".join(
                    [
                        self.template_parser.get(
                            "Rag",
                            "database_prompt",
                            {"db_num": idx + 1, "chunk_text": db.text},
                        )
                        for idx, db in enumerate(retrived_document)
                    ]
                )
                
                database_prompt = f"""
## 🚗 SEARCH RESULTS (Available Cars):
{database_results}

Note: These cars will appear in a 'cars' list below your message if you recommend them.
"""
                print(f"✅ Sending {len(retrived_document)} cars to LLM")
            else:
                database_prompt = ""
                print(f" No cars found in search")          

            system_prompt = self.template_parser.get("Rag", "system_prompt")
            footer_prompt = self.template_parser.get("Rag", "footer_prompt")

            # 🔥 DYNAMIC INSTRUCTION: Only tell LLM to show cars if we actually found them
            if retrived_document and len(retrived_document) > 0:
                footer_prompt += "\n\nمهم جداً: بما إن فيه نتايج عربيات ظهرت في البحث، لازم وأنت بتشرح أي عربية منهم تقول في آخر كلامك: 'شوف الخيارات دي!' عشان تظهر ككارت لليوزر."
                footer_prompt += "\nتنبيه: لو العميل سأل عن عربية واحدة، اشرحها هي بس ومتتكلمش عن العربيات التانية اللي ظهرت في البحث."

            user_question_section = f"\n\n## User Question:\n{message}\n"

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

            answer = self.generation_client.generate_text(
                prompt=full_prompt,
                chat_history=chat_history,
            )

            if answer:
                memory.add_user_message(message)
                memory.add_ai_message(answer)

        except Exception as e:
            print(f"Error in Anser_Rag_question: {str(e)}")
            traceback.print_exc()
            answer = None
            retrived_document = []

        print(f"\n📤 [RETURN] Returning {len(retrived_document)} documents to API")
        return answer, full_prompt, self._memory_to_dict(memory), retrived_document


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
