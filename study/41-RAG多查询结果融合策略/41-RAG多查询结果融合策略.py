import os
from typing import List
import dotenv
import weaviate
from langchain.load import dumps, loads
from langchain.retrievers import MultiQueryRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_weaviate import WeaviateVectorStore

dotenv.load_dotenv(override=True)

import json


def safe_load(doc):
    """确保 doc 中的 UUID 转换为字符串"""
    try:
        if (
            isinstance(doc, dict)
            and "id" in doc
            and isinstance(doc["id"], list)
            and "UUID" in doc["id"]
        ):
            doc["id"] = str(doc["id"])  # 转换 UUID
        return json.loads(doc)
    except Exception as e:
        print(f"Error parsing document: {e}")
        return None


class RAGFusionRetriever(MultiQueryRetriever):
    """RAG多查询结果融合策略检索器"""

    k: int = 4

    def retrieve_documents(
        self, queries: List[str], run_manager: CallbackManagerForRetrieverRun
    ) -> List[List]:
        """重写检索文档函数，返回值变成一个嵌套的列表"""
        documents = []
        for query in queries:
            docs = self.retriever.invoke(
                query, config={"callbacks": run_manager.get_child()}
            )
            documents.append(docs)
        return documents

    def unique_union(self, documents: List[List]) -> List[Document]:
        """使用RRF算法来去重合并对应的文档，参数为嵌套列表，返回值为文档列表"""
        # 1.定义一个变量存储每个文档的得分信息
        fused_result = {}

        # 2.循环两层获取每一个文档信息
        for docs in documents:
            for rank, doc in enumerate(docs):
                # 3.使用dumps函数将类示例转换成字符串
                doc_str = dumps(doc)
                # 4.判断下该文档的字符串是否已经计算过得分
                if doc_str not in fused_result:
                    fused_result[doc_str] = 0
                # 5.计算新的分
                fused_result[doc_str] += 1 / (rank + 60)

        # 6.执行排序操作，获取相应的数据，使用的是降序
        reranked_results = [
            (safe_load(doc), score)
            for doc, score in sorted(
                fused_result.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return [item[0] for item in reranked_results[: self.k]]


embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_base=os.getenv("OPENAI_API_BASE"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
)

db = WeaviateVectorStore(
    client=client,
    index_name="DatasetDemo",
    text_key="text",
    embedding=embedding,
)

retriever = db.as_retriever(search_type="mmr")

rag_fusion_retriever = RAGFusionRetriever.from_llm(
    retriever=retriever,
    llm=ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0,
    ),
)

docs = rag_fusion_retriever.invoke("关于HTTP配置的信息有哪些")

print(docs)
print(len(docs))

client.close()
