from typing import Literal
import os
import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

dotenv.load_dotenv(override=True)


class RouteQuery(BaseModel):
    """将用户查询映射到对应数据源"""

    datasource: Literal["python_docs", "js_docs", "golang_docs"] = Field(
        description="根据用户的问题，选择哪个数据源最相关"
    )


llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
    temperature=0,
)

structured_llm = llm.with_structured_output(RouteQuery)


question = """为什么下面的代码报错，请帮我检查一下:
import { Message } from '@arco-design/web-vue'
  // 当上一条消息为加载状态时，不允许发送新消息
  if (messages.value.length && isLoading.value) {
    Message.error('请等待上一条消息加载完成')
    return
  }
"""

res = structured_llm.invoke(question)

print(res)
