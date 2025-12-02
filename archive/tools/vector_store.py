"""
向量存储工具 - 基于 Chroma 的文档向量化和检索
为知识管理专家提供支持
"""

import os
from typing import List, Dict, Optional, Any
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
import hashlib
import json

load_dotenv()


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        初始化向量存储管理器
        
        Args:
            persist_directory: 向量数据库持久化目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 Google 嵌入模型
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ 未设置 GEMINI_API_KEY")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        
        # 初始化向量存储
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="agentdesk_documents"
        )
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
    
    def add_document(self, file_path: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        添加文档到向量存储
        
        Args:
            file_path: 文档路径
            metadata: 额外的元数据
        
        Returns:
            添加结果
        """
        try:
            # 读取文档内容
            content = self._load_document(file_path)
            
            if not content:
                return {
                    "success": False,
                    "error": "无法读取文档内容"
                }
            
            # 生成文档ID（基于内容哈希）
            doc_id = self._generate_doc_id(content)
            
            # 分割文档
            chunks = self.text_splitter.split_text(content)
            
            # 准备文档和元数据
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "source": os.path.basename(file_path),
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **(metadata or {})
                }
                documents.append(
                    Document(page_content=chunk, metadata=doc_metadata)
                )
            
            # 添加到向量存储
            ids = self.vector_store.add_documents(documents)
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_count": len(chunks),
                "vector_ids": ids
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search(self, query: str, k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_metadata: 元数据过滤条件
        
        Returns:
            搜索结果列表
        """
        try:
            # 执行相似度搜索
            if filter_metadata:
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=k,
                    filter=filter_metadata
                )
            else:
                results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            return formatted_results
        
        except Exception as e:
            print(f"搜索错误: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[List[Dict]]:
        """
        根据文档ID获取所有分块
        
        Args:
            doc_id: 文档ID
        
        Returns:
            文档分块列表
        """
        try:
            results = self.vector_store.get(
                where={"doc_id": doc_id}
            )
            
            if not results or not results.get('documents'):
                return None
            
            # 组合结果
            chunks = []
            for i, (content, metadata) in enumerate(zip(
                results['documents'],
                results['metadatas']
            )):
                chunks.append({
                    "content": content,
                    "metadata": metadata,
                    "chunk_index": metadata.get('chunk_index', i)
                })
            
            # 按 chunk_index 排序
            chunks.sort(key=lambda x: x['chunk_index'])
            return chunks
        
        except Exception as e:
            print(f"获取文档错误: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            是否成功
        """
        try:
            self.vector_store.delete(
                where={"doc_id": doc_id}
            )
            return True
        except Exception as e:
            print(f"删除文档错误: {e}")
            return False
    
    def list_documents(self) -> List[Dict]:
        """
        列出所有文档
        
        Returns:
            文档列表
        """
        try:
            # 获取所有文档的元数据
            results = self.vector_store.get()
            
            if not results or not results.get('metadatas'):
                return []
            
            # 按 doc_id 去重
            docs_map = {}
            for metadata in results['metadatas']:
                doc_id = metadata.get('doc_id')
                if doc_id and doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "doc_id": doc_id,
                        "source": metadata.get('source', 'unknown'),
                        "total_chunks": metadata.get('total_chunks', 0)
                    }
            
            return list(docs_map.values())
        
        except Exception as e:
            print(f"列出文档错误: {e}")
            return []
    
    def _load_document(self, file_path: str) -> Optional[str]:
        """加载文档内容"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.pdf':
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                return "\n\n".join([p.page_content for p in pages])
            elif ext in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
                return "\n\n".join([d.page_content for d in docs])
            else:
                # 尝试作为文本读取
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"加载文档失败 {file_path}: {e}")
            return None
    
    def _generate_doc_id(self, content: str) -> str:
        """生成文档ID（基于内容哈希）"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()


# 全局实例
vector_store_manager = VectorStoreManager()


__all__ = [
    "VectorStoreManager",
    "vector_store_manager"
]

