import numpy as np
import os
import dotenv
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain_openai import OpenAIEmbeddings

dotenv.load_dotenv()


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """计算余弦相似度"""
    # 计算向量的点积
    dot_product = np.dot(v1, v2)

    # 计算向量的模
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    # 计算余弦相似度
    cosine_similarity = dot_product / (norm_v1 * norm_v2)

    return cosine_similarity


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_base=os.getenv("OPENAI_API_BASE"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)  # 创建文本嵌入模型
embeddings_with_cache = CacheBackedEmbeddings.from_bytes_store(
    embeddings,
    LocalFileStore("./storage/cache"),
    namespace=embeddings.model,
    query_embedding_cache=True,
)

query_vector = embeddings_with_cache.embed_query("liu喜欢看书")  # 编码文本

print(query_vector)  # 打印编码后的文本向量
print(len(query_vector))  # 打印文本向量的长度

documents_vectors = embeddings_with_cache.embed_documents(
    [
        "我是liu,我喜欢看书",
        "这个喜欢看书的人是liu",
        "学习是一种乐趣",
    ]
)

print(len(documents_vectors))  # 打印文档向量的长度

print(
    cosine_similarity(query_vector, documents_vectors[0])
)  # 计算文本向量与第一个文档向量的余弦相似度
print(
    cosine_similarity(query_vector, documents_vectors[1])
)  # 计算文本向量与第二个文档向量的余弦相似度
print(
    cosine_similarity(query_vector, documents_vectors[2])
)  # 计算文本向量与第三个文档向量的余弦相似度
print(
    cosine_similarity(documents_vectors[0], documents_vectors[1])
)  # 计算第一个文档向量与第二个文档向量的余弦相似度
print(
    cosine_similarity(documents_vectors[0], documents_vectors[2])
)  # 计算第一个文档向量与第三个文档向量的余弦相似度
print(
    cosine_similarity(documents_vectors[1], documents_vectors[2])
)  # 计算第二个文档向量与第三个文档向量的余弦相似度
