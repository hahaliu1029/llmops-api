import os
import dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

embeddings = HuggingFaceEmbeddings(
    model_name="Alibaba-NLP/gte-modernbert-base",
    cache_folder="./storage/cache",
)

dotenv.load_dotenv()

# embeddings = OpenAIEmbeddings(
#     model="text-embedding-3-small",
#     openai_api_base=os.getenv("OPENAI_API_BASE"),
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
# )

# db = FAISS.from_texts(
#     [
#         "笨笨是一只很喜欢睡觉的猫咪",
#         "我喜欢在夜晚听音乐，这让我感到放松。",
#         "猫咪在窗台上打盹，看起来非常可爱。",
#         "学习新技能是每个人都应该追求的目标。",
#         "我最喜欢的食物是意大利面，尤其是番茄酱的那种。",
#         "昨晚我做了一个奇怪的梦，梦见自己在太空飞行。",
#         "我的手机突然关机了，让我有些焦虑。",
#         "阅读是我每天都会做的事情，我觉得很充实。",
#         "他们一起计划了一次周末的野餐，希望天气能好。",
#         "我的狗喜欢追逐球，看起来非常开心。",
#     ],
#     embeddings,
#     relevance_score_fn=lambda distance: 1 / (1 + distance),
# )

# # print(db.index.ntotal)

# print(db.similarity_search_with_relevance_scores("我的猫叫笨笨"))

texts: list = [
    "笨笨是一只很喜欢睡觉的猫咪",
    "我喜欢在夜晚听音乐，这让我感到放松。",
    "猫咪在窗台上打盹，看起来非常可爱。",
    "学习新技能是每个人都应该追求的目标。",
    "我最喜欢的食物是意大利面，尤其是番茄酱的那种。",
    "昨晚我做了一个奇怪的梦，梦见自己在太空飞行。",
    "我的手机突然关机了，让我有些焦虑。",
    "阅读是我每天都会做的事情，我觉得很充实。",
    "他们一起计划了一次周末的野餐，希望天气能好。",
    "我的狗喜欢追逐球，看起来非常开心。",
]
metadatas: list = [
    {"page": 1},
    {"page": 2},
    {"page": 3},
    {"page": 4},
    {"page": 5},
    {"page": 6},
    {"page": 7},
    {"page": 8},
    {"page": 9},
    {"page": 10},
]

db = PineconeVectorStore(
    index_name="llmops-768", embedding=embeddings, namespace="dataset"
)

# db.add_texts(texts, metadatas, namespace="dataset")

query = "我的猫叫笨笨"

print(
    db.similarity_search_with_relevance_scores(
        query,
        filter={"page": {"$lte": 5}},
    )
)
