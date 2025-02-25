import os
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from internal.entity.conversation_entity import SUMMARIZER_TEMPLATE


@inject
@dataclass
class ConversationService(BaseService):
    """会话服务"""

    db: SQLAlchemy

    @classmethod
    def summary(cls, human_message: str, ai_message: str, old_summary: str = "") -> str:
        """根据传递的人类消息、AI消息还有原始的摘要，生成新的摘要"""
        # 创建prompt
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)

        # 构建大语言模型实例，并将大语言模型温度调低，降低幻觉的概率
        llm = ChatOpenAI(
            temperature=0.5,
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE"),
        )

        # 构建链应用
        summary_chain = prompt | llm | StrOutputParser()

        # 调用链并获取新摘要信息
        new_summary = summary_chain.invoke(
            {
                "summary": old_summary,
                "new_lines": f"Human: {human_message}\nAI: {ai_message}",
            }
        )

        return new_summary
