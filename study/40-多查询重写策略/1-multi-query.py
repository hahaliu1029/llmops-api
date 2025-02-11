import os
import dotenv
import weaviate
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_weaviate import WeaviateVectorStore
from langchain_core.prompts import (
    ChatPromptTemplate,
)

dotenv.load_dotenv(override=True)

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

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
    temperature=0,
)

# 创建多查询检索器
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=llm,
    include_original=True,
    prompt=ChatPromptTemplate.from_template(
        "你是一个AI语言模型助手。你的任务是生成给定用户问题的3个不同版本，以从向量数据库中检索相关文档。"
        "通过提供用户问题的多个视角，你的目标是帮助用户克服基于距离的相似性搜索的一些限制。"
        "请用换行符分隔这些替代问题。"
        "原始问题：{question}"
    ),
)


docs = multi_query_retriever.invoke("关于HTTP配置的信息有哪些")

print(docs)
print(len(docs))

client.close()
