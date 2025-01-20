import os
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

dotenv.load_dotenv()

# 1. 编排prompt
joke_prompt = ChatPromptTemplate.from_template("请讲一个关于{subject}的笑话, 短一些")
poem_prompt = ChatPromptTemplate.from_template("请写一首关于{subject}的诗，短一些")

# 2. 创建大语言模型
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

# 3. 创建输出解析器
parser = StrOutputParser()

# 4. 编排链
joke_chain = joke_prompt | llm | parser
poem_chain = poem_prompt | llm | parser

# 5. 并行调用
map_chain = RunnableParallel(
    {"joke": joke_chain, "poem": poem_chain}
)  # 并行调用 joke_chain 和 poem_chain

# 6. 调用链
res = map_chain.invoke({"subject": "猫"})

print(res)
