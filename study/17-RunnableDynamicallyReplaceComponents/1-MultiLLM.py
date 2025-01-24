import os
import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField

dotenv.load_dotenv()

prompt = ChatPromptTemplate.from_template("{query}")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
).configurable_alternatives(
    ConfigurableField(
        id="llm",
        name="llm",
        description="The language model to use",
    ),
    default_key="deepseek-chat",
    gpt3=ChatOpenAI(
        model="gpt-3.5-turbo-16k",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE"),
    ),
    gpt4=ChatOpenAI(
        model="gpt-4o",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE"),
    ),
)

chain = prompt | llm | StrOutputParser()

content = chain.invoke(
    "你使用了什么模型进行训练和回复？", config={"configurable": {"llm": "gpt4"}}
)

print(content)
