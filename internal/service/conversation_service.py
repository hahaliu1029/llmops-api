import logging
import os
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
)


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

    @classmethod
    def generate_conversation_name(cls, query: str) -> str:
        """根据传递的query生成对应会话名字，并且语言与用户的输入保持一致"""
        # 创建prompt
        prompt = ChatPromptTemplate.from_messages(
            [("system", CONVERSATION_NAME_TEMPLATE), ("human", "{query}")]
        )

        # 构建大语言模型实例，并将大语言模型温度调低，降低幻觉的概率
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            # model="moonshot-v1-8k",
            # temperature=0,
            # openai_api_key=os.getenv("KIMI_API_KEY"),
            # openai_api_base=os.getenv("KIMI_API_BASE"),
        )
        structured_llm = llm.with_structured_output(ConversationInfo)

        # 构建链应用
        chain = prompt | structured_llm

        # 提取并整理query，截取长度过长的部分
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]..." + query[-300:]

        query = query.replace("\n", "")

        # 调用链并获取会话信息
        conversation_info = chain.invoke({"query": query})

        # 提取会话名称
        name = "新的会话"
        try:
            if conversation_info and hasattr(conversation_info, "subject"):
                name = conversation_info.subject
        except Exception as e:
            logging.exception(
                f"提取会话名称出错，conversation_info: {conversation_info}, 错误信息: {str(e)}"
            )

        if len(name) > 75:
            name = name[:75] + "..."

        return name
