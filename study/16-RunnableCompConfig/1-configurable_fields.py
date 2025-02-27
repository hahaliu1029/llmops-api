import os
import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField

dotenv.load_dotenv(override=True)

prompt = PromptTemplate.from_template("请生成一个小于{x}的随机整数")

llm = ChatOpenAI(
    model="cursor-3-5-sonnet-20240620",
    openai_api_key=os.getenv("YUNWU_API_KEY"),
    openai_api_base=os.getenv("YUNWU_API_BASE"),
).configurable_fields(
    temperature=ConfigurableField(
        id="llm_temperature",
        name="温度",
        description="温度越低，生成的文本越保守， 越高则生成的文本越大胆",
    )
)

chain = prompt | llm | StrOutputParser()

content = chain.invoke({"x": 1000})

print(content)

print("======================")

content = chain.invoke({"x": 1000}, config={"configurable": {"llm_temperature": 0}})

print(content)

print("======================")

with_config_chain = chain.with_config({"configurable": {"llm_temperature": 0}})

content = with_config_chain.invoke({"x": 1000})

print(content)
