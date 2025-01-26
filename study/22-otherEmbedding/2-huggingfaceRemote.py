import dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings

dotenv.load_dotenv()

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2"
)

query_vector = embeddings.embed_query("liu喜欢看书")  # 编码文本

print(query_vector)  # 打印编码后的文本向量
print(len(query_vector))  # 打印文本向量的长度
