from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)

from langchain_community.chat_message_histories import (
    PostgresChatMessageHistory,
)

chat_history = InMemoryChatMessageHistory()

chat_history.add_user_message("你好，我是liu, 你是谁？")
chat_history.add_ai_message("你好，我是一个聊天机器人。")

print(chat_history.messages)
