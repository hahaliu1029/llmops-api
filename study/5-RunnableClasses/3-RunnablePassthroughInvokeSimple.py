import os
import dotenv
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

dotenv.load_dotenv()


def retrieval(query: str) -> str:
    return "这是一个关于" + query + "的回答"


# 1. 编排prompt
prompt = ChatPromptTemplate.from_template(
    """请根据用户的问题回答。可以参考对应上下文进行生成。
                                          
                                          <context>
                                          {context}
                                          </context>

                                          用户的提问是：{query}
                                          """
)

# 2. 创建大语言模型
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

# 3. 创建输出解析器
parser = StrOutputParser()

# 4. 编排链
chain = (
    RunnablePassthrough.assign(
        context=lambda x: retrieval(x["query"]),
    )
    | prompt
    | llm
    | parser
)

# 5. 调用
content = chain.invoke(
    {
        "query": "我是谁？",
    }
)

print(content)
