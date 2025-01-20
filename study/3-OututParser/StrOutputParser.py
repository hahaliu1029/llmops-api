import os
import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.prompts import ChatPromptTemplate

dotenv.load_dotenv()  # Load the environment variables from the .env file

prompt = ChatPromptTemplate.from_template("{query}")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

parser = StrOutputParser()

# content = parser.parse("你好, 请帮我推荐一款适合学习的编程语言")

# print(content)

content = parser.invoke(llm.invoke(prompt.invoke({"query": "你好, 你是？"})))

print(content)
