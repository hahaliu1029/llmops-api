from operator import itemgetter
import os
from typing import Any, Dict
import uuid
from dataclasses import dataclass
from flask import request
from injector import inject

from internal.schema.app_schema import CompletionReq
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
    fail_message,
)
from internal.exception import FailException
from internal.service import AppService, VectorDatabaseService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import (
    ConversationBufferWindowMemory,
)
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.memory import BaseMemory
from langchain_core.tracers.schemas import Run


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService
    vector_database_service: VectorDatabaseService

    def create_app(self):
        """创建应用"""
        app = self.app_service.create_app()
        return success_message(f"创建应用成功，应用ID为{app.id}")

    def ping(self):
        # providers = self.provider_factory.get_provider_entities()
        return success_json()
        # return {"ping": "pong"}

    @classmethod
    def _load_memory_variables(
        cls, input: Dict[str, Any], config: RunnableConfig
    ) -> Dict[str, Any]:
        """加载记忆变量"""
        # 从config中获取configurable
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(
            configurable_memory, BaseMemory
        ):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """保存上下文"""
        # 从config中获取configurable
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        print(run_obj.inputs)
        print(run_obj.outputs)
        if configurable_memory is not None and isinstance(
            configurable_memory, BaseMemory
        ):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    def debug(self, app_id: uuid.UUID):
        """聊天接口"""
        # 1. 获取输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 创建prompt与记忆
        system_prompt = "你是一个聊天机器人，能根据对应的上下文和历史对话信息回复用户问题。\n\n<context>{context}</context>"
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("history"),
                ("human", "{query}"),
            ]
        )
        memory = ConversationBufferWindowMemory(
            k=3,
            return_messages=True,
            input_key="query",
            output_key="output",
            chat_memory=FileChatMessageHistory("./storage/memory/chat_memory.txt"),
        )

        llm = ChatOpenAI(
            # model="gpt-3.5-turbo-16k",
            # openai_api_key=os.getenv("OPENAI_API_KEY"),
            # openai_api_base=os.getenv("OPENAI_API_BASE"),
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        )

        # prompt = ChatPromptTemplate.from_template("{query}")

        retriever = (
            self.vector_database_service.get_retriever()
            | self.vector_database_service.combine_documents
        )
        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(self._load_memory_variables)
                | itemgetter("history"),
                context=itemgetter("query") | retriever,
            )
            | prompt
            | llm
            | StrOutputParser()
        ).with_listeners(on_end=self._save_context)

        chain_input = {"query": request.json["query"]}
        content = chain.invoke(
            chain_input,
            config={
                "configurable": {
                    "memory": memory,
                }
            },
        )
        # memory.save_context(chain_input, {"output": content})

        # 2. 构建DEEPSEEK客户端，调用接口
        # client = OpenAI(
        #     api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     base_url=os.getenv("DEEPSEEK_API_BASE"),
        # )
        # llm = ChatOpenAI(
        #     model="deepseek-chat",
        #     openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        # )

        # parser = StrOutputParser()

        # # 3. 得到结果，返回

        # chain = prompt | llm | parser

        # # ai_message = llm.invoke(prompt.invoke({"query": request.json["query"]}))

        # # content = parser.invoke(ai_message)

        # # response = client.chat.completions.create(
        # #     model="deepseek-chat",
        # #     messages=[
        # #         {
        # #             "role": "system",
        # #             "content": "你是一个聊天机器人，请根据用户输入回复信息",
        # #         },
        # #         {"role": "user", "content": request.json["query"]},
        # #     ],
        # #     stream=False,
        # # )
        # # content = response.choices[0].message.content

        # content = chain.invoke({"query": request.json["query"]})

        return success_json({"content": content})

    def get_app(self, id: uuid.UUID):
        """获取应用"""
        app = self.app_service.get_app(id)
        return success_message(f"获取应用成功，应用ID为{app.id}, 应用名称为{app.name}")

    def update_app(self, id: uuid.UUID):
        """更新应用"""
        app = self.app_service.update_app(id)
        return success_message(f"更新应用成功，应用ID为{app.id}, 应用名称为{app.name}")

    def delete_app(self, id: uuid.UUID):
        """删除应用"""
        try:
            app = self.app_service.delete_app(id)
        except Exception as e:
            return fail_message(f"删除应用失败，应用ID为{id}, 错误信息为{str(e)}")
        return success_message(f"删除应用成功，应用ID为{app.id}, 应用名称为{app.name}")
