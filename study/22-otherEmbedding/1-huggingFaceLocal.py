from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="Alibaba-NLP/gte-modernbert-base",
    cache_folder="./storage/cache",
)

query_vector = embeddings.embed_query("liu喜欢看书")  # 编码文本

print(query_vector)  # 打印编码后的文本向量
print(len(query_vector))  # 打印文本向量的长度
