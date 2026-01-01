from .BaseControlls import BaseControlls
from .ProjectControllers import ProjectControllers
from fastapi import FastAPI, APIRouter, Depends, UploadFile
import os
from models.Enums import ProcessingEnumertion
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.json_loader import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter 



class ProcessControlles(BaseControlls):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        # strip accidental whitespace from returned path
        self.project_path = ProjectControllers().get_project_path(project_id=project_id).strip()
    
    def get_file_Extention(self, file_id: str):
        # validate early
        if file_id is None:
            raise ValueError("file_id is required and cannot be None")
        if not isinstance(file_id, (str, bytes, os.PathLike)):
            raise TypeError("file_id must be a string or path-like object")
        return os.path.splitext(str(file_id))[1].lower()
    
    def get_file_loader(self, file_id: str):
        # normalize and validate
        if file_id is None:
            raise ValueError("file_id is required")
        if isinstance(file_id, str):
            file_id = file_id.strip()

        file_ext = self.get_file_Extention(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        # normalize enum values
        def _norm_ext(val: str):
            v = val.lower()
            return v if v.startswith('.') else f".{v}"

        csv_val = _norm_ext(ProcessingEnumertion.ProcessingEnums.CSV.value)
        json_val = _norm_ext(ProcessingEnumertion.ProcessingEnums.JSON.value)

        if file_ext == csv_val:
            return CSVLoader(file_path, encoding='utf-8-sig')
        if file_ext == json_val:
            # 🔥 Fix: Ensure rag_content exists
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                modified = False
                if isinstance(data, list):
                    for item in data:
                        if 'rag_content' not in item and isinstance(item, dict):
                            # Generate rag_content form available fields
                            name = item.get('name', '')
                            price = item.get('price', '')
                            specs = item.get('structured_details') or item.get('specs') or {}
                            
                            specs_str = ""
                            if isinstance(specs, dict):
                                specs_list = []
                                # Mapping common keys to Arabic for better RAG
                                for k, v in specs.items():
                                    if v:
                                        specs_list.append(f"{k}: {v}")
                                specs_str = ", ".join(specs_list)
                            
                            item['rag_content'] = f"السيارة: {name}. السعر: {price}. المواصفات: {specs_str}."
                            modified = True
                
                if modified:
                    print(f"🔧 Auto-generated rag_content for file: {file_id}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ Error ensuring rag_content: {e}")

            return JSONLoader(
                file_path, 
                jq_schema='.[]',
                content_key='rag_content',
                text_content=False
            )

        return None
        
    

    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader :
            return loader.load()
     
        return None
    


    def split_file_content(self, file_content : list ,file_id: str, chunk_size: int = 100, chunk_overlap: int=20):
        """
        تقسيم المحتوى إلى chunks.
        لو chunk_size أكبر من طول المحتوى، كل document هيكون chunk واحد.
        """
        all_small = all(len(rec.page_content) <= chunk_size for rec in file_content)
        
        if all_small and chunk_overlap == 0:
            return file_content

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
            )
        file_content_list = [rec.page_content for rec in file_content]
        file_metadata_list = [rec.metadata for rec in file_content]
        
        chunks = text_splitter.create_documents(
            file_content_list,
            metadatas=file_metadata_list
            )
        return chunks
        