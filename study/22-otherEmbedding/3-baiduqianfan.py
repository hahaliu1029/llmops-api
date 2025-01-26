import dotenv
from langchain_community.embeddings.baidu_qianfan_endpoint import (
    QianfanEmbeddingsEndpoint,
)

dotenv.load_dotenv()

embeddings = QianfanEmbeddingsEndpoint()

query_vector = embeddings.embed_query("liu喜欢看书")

print(query_vector)
print(len(query_vector))
