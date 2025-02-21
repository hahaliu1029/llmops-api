from http import client
import os
import dotenv
import weaviate
from weaviate.auth import AuthApiKey
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter
from langchain_openai import OpenAIEmbeddings
from weaviate.classes.config import DataType

dotenv.load_dotenv(override=True)

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
    {"page": 6, "account_id": 1},
    {"page": 7},
    {"page": 8},
    {"page": 9},
    {"page": 10},
]

client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
)

# 删除已有的 Dataset 类（如果存在）
try:
    client.collections.delete("Dataset")
except Exception as e:
    print(f"❗忽略删除错误：{e}")

# 重新创建 Dataset 类，✅ 这里修正 data_type
client.collections.create(
    name="Dataset",
    properties=[
        {"name": "text", "data_type": DataType.TEXT},  # ✅ 使用 DataType.TEXT
        {"name": "account_id", "data_type": DataType.UUID},  # ✅ 使用 DataType.STRING
    ],
)

print("✅ Schema 更新完成")
# client = weaviate.connect_to_wcs(
#     cluster_url="https://d06gk6iwtssfxu50fov2ta.c0.us-west3.gcp.weaviate.cloud",
#     auth_credentials=AuthApiKey("rwOwzVdNRvhqeCykTGOA9cm2OQv2al6OtI6e"),
# )

# embedding = HuggingFaceEmbeddings(
#     model_name="Alibaba-NLP/gte-modernbert-base",
# )

# embedding = OpenAIEmbeddings(
#     model="text-embedding-3-small",
#     openai_api_base=os.getenv("OPENAI_API_BASE"),
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
# )

# # 创建langchain向量数据库实例
# db = WeaviateVectorStore(
#     client=client,
#     index_name="Dataset",
#     text_key="text",
#     embedding=embedding,
# )

# # 向数据库中添加数据
# ids = db.add_texts(texts, metadatas)

# print(ids)

# # 从数据库中搜索相似文本
# filters = Filter.by_property("page").greater_or_equal(5)
# results = db.similarity_search_with_score("我的猫叫笨笨", filters=filters)
# print(results)
