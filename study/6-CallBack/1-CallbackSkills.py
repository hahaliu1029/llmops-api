import os
from typing import Any, Dict, List, Optional
from uuid import UUID
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.callbacks import StdOutCallbackHandler, BaseCallbackHandler
from langchain_core.messages import BaseMessage

dotenv.load_dotenv()


class LLMOpsCallbackHandler(BaseCallbackHandler):
    """自定义LLMOps回调处理程序"""

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """当聊天模型开始时运行"""
        print(f"聊天模型开始, run_id: {run_id}")
        print("serialized: ", serialized)
        # print("messages: ", messages)


# 1. 编排prompt
prompt = ChatPromptTemplate.from_template("{query}")

# 2. 创建大语言模型
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
)

# 3. 构建链
chain = {"query": RunnablePassthrough()} | prompt | llm | StrOutputParser()

# 4. 调用
content = chain.invoke(
    "你好, 你是？",
    config={"callbacks": [StdOutCallbackHandler(), LLMOpsCallbackHandler()]},
)

print(content)
