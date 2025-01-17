from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import AIMessage
from datetime import datetime

prompt = PromptTemplate.from_template("讲一个{subject}实用技巧")
print(prompt.format(subject="Python"))
prompt_value = prompt.invoke({"subject": "Python"})

print(prompt_value.to_string())
print(prompt_value.to_json())
print(prompt_value.to_messages())


print("--------------------------------------------------")

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个聊天机器人，请根据用户的提问进行回复，当前的时间为:{now}"),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template("你好，我想了解{subject}的实用技巧"),
    ]
).partial(now=datetime.now())

chat_prompt_value = chat_prompt.invoke(
    {
        "chat_history": [
            ("user", "aaaaaa"),
            AIMessage("你好，我是一个聊天机器人，请问有什么可以帮助你的？"),
        ],
        "subject": "Python",
    }
)

print(chat_prompt_value.to_string())
