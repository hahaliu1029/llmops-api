import os
import dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

dotenv.load_dotenv()


# 1. 创建一个json数据结构，告诉大语言模型json长什么样
class Joke(BaseModel):
    joke: str = Field(description="The joke text")
    punchline: str = Field(description="The punchline text")


parser = JsonOutputParser(
    pydantic_object=Joke,
)

# 2. 创建一个模板，告诉大语言模型如何生成json数据
prompt = ChatPromptTemplate.from_template(
    "请根据用户的提问进行回答。 \n{format_instructions}\n{query}"
).partial(format_instructions=parser.get_format_instructions())

# print(prompt.format(query="请讲一个笑话"))

# 3.构建一个大语言模型
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

# 4.传递提示并进行解析
ai_message = llm.invoke(prompt.invoke({"query": "请讲一个笑话"}))

joke = parser.invoke(ai_message)

print(joke)
