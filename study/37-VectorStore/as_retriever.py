import os
import dotenv
import weaviate
from langchain_community.document_loaders import (
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
)
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey

dotenv.load_dotenv(override=True)

# word_loader = UnstructuredWordDocumentLoader(
#     "./副本元脑服务器 G8系列 InBry Redfish用户手册 V1.0-20241126-联合管理-20241202(3).docx",
#     mode="paged",
# )

# documents = word_loader.load()

loader = UnstructuredMarkdownLoader("./README.md")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    separators=[
        "\n\n",
        "\n",
        "。|！|？",
        "\.\s|\!\s|\?\s",
        "；|;\s",
        "，|,\s",
        " ",
        "",
    ],
    is_separator_regex=True,
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
)

chunks = text_splitter.split_documents(documents)

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

db.add_documents(chunks)

# 4.转换检索器（带阈值的相似性搜索，数据为10条，得分阈值为0.5）
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 10, "score_threshold": 0.5},
)

# 5.检索结果
documents = retriever.invoke("关于HTTP配置的信息有哪些")

print(list(document.page_content[:50] for document in documents))
print(len(documents))

client.close()
