from operator import itemgetter
import os
import dotenv
from flask_migrate import history
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
)
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

dotenv.load_dotenv()

# Create a new ChatPromptTemplate object
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个聊天机器人，请根据对应的上下文回答问题。"),
        MessagesPlaceholder("history"),
        ("human", "{query}"),
    ]
)
memory = ConversationSummaryBufferMemory(
    max_token_limit=300,
    return_messages=True,
    input_key="query",
    llm=ChatOpenAI(
        model="gpt-3.5-turbo-16k",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE"),
    ),
)


# Create a new ChatOpenAI object
# memory_variable = memory.load_memory_variables({})
llm = ChatOpenAI(
    model="gpt-3.5-turbo-16k",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE"),
)

# Build the chain
chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
    )
    | prompt
    | llm
    | StrOutputParser()
)

# 死循环构建对话命令行
while True:
    query = input("Human: ")

    if query == "q":
        break

    chain_input = {"query": query}

    response = chain.stream(chain_input)
    print(response)  # 检查返回的数据是否为空

    print("Bot: ", flush=True, end="")
    output = ""
    for chunk in response:
        output += chunk
        print(chunk, flush=True, end="")
    memory.save_context(chain_input, {"output": output})
    print("")
    print("history: ", memory.load_memory_variables({}))
