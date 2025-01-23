import os
import dotenv

from flask import session
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

dotenv.load_dotenv()

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = FileChatMessageHistory("./" + session_id + ".json")
    return store[session_id]


# 创建提示模版与大模型
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个聊天机器人，请根据用户输入回复信息"),
        MessagesPlaceholder("history"),
        ("human", "{query}"),
    ]
)

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

# 构建链式调用
chain = prompt | llm | StrOutputParser()

with_message_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="query",
    history_messages_key="history",
)

while True:
    query = input("Human: ")

    if query == "q":
        exit(0)

    response = with_message_chain.stream(
        {"query": query},
        config={
            "configurable": {
                "session_id": "test_session_id",
            }
        },
    )

    print("AI: ", flush=True, end="")

    for chunk in response:
        print(chunk, flush=True, end="")
    print("")
