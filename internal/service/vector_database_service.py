import os
from typing import List
from injector import inject
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient
import weaviate
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from .embeddings_service import EmbeddingsService
from weaviate.collections import Collection


# 向量数据库的集合名字
COLLECTION_NAME = "Dataset"


@inject
class VectorDatabaseService:
    """向量数据库服务"""

    client: WeaviateClient
    vector_store: WeaviateVectorStore
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        """完成向量数据库服务的客户端+LangChain向量数据库实例的创建"""

        # 赋值文本嵌入模型服务
        self.embeddings_service = embeddings_service

        # 创建Weaviate客户端
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT")),
        )

        # 创建LangChain向量数据库实例
        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=self.embeddings_service.embeddings,
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取向量数据库服务的检索器"""
        return self.vector_store.as_retriever()

    @classmethod
    def combine_documents(cls, documents: List[Document]) -> str:
        """将对应的文档列表使用换行符进行合并"""
        return "\n\n".join([document.page_content for document in documents])

    @property
    def collection(self) -> Collection:
        """获取向量数据库服务的集合名"""
        return self.client.collections.get(COLLECTION_NAME)
