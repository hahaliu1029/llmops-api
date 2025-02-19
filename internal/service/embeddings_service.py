import os
from injector import inject
from dataclasses import dataclass
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain.embeddings import CacheBackedEmbeddings
from redis import Redis
from langchain_openai import OpenAIEmbeddings
import tiktoken
from langchain_huggingface import HuggingFaceEmbeddings


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""

    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(
            client=redis,
        )
        self._embeddings = HuggingFaceEmbeddings(
            model_name="Alibaba-NLP/gte-multilingual-base",
            cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
            model_kwargs={"trust_remote_code": True},
        )
        # self._embeddings = OpenAIEmbeddings(
        #     model="text-embedding-3-small",
        #     openai_api_base=os.getenv("OPENAI_API_BASE"),
        #     openai_api_key=os.getenv("OPENAI_API_KEY"),
        # )
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.encoding_for_model("gpt-3.5")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        """获取存储器"""
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        """获取文本嵌入模型客户端"""
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        """获取缓存客户端"""
        return self._cache_backed_embeddings
