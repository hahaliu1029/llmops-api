from datetime import datetime
import os
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAI

dotenv.load_dotenv()  # Load the environment variables from the .env file

# 1. 编排对话模版
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个机器人，请回答用户的问题, 现在的时间是{now}"),
        ("human", "{query}"),
    ]
).partial(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 2. 创建大语言模型
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

ai_messages = llm.batch(
    [
        prompt.invoke({"query": "你好, 你是？"}),
        prompt.invoke({"query": "你好, 请帮我推荐一款适合学习的编程语言"}),
    ]
)

for ai_message in ai_messages:
    print(ai_message.content)
    print("^^^^^^^^^^^^^^^^^^^^^^^")
