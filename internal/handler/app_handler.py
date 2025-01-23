from operator import itemgetter
import os
import uuid
from dataclasses import dataclass
from flask import request, jsonify
from injector import inject
from openai import OpenAI

from internal.schema.app_schema import CompletionReq
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
    fail_message,
)
from internal.exception import FailException
from internal.service import AppService
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import (
    ConversationBufferWindowMemory,
)
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService

    def create_app(self):
        """创建应用"""
        app = self.app_service.create_app()
        return success_message(f"创建应用成功，应用ID为{app.id}")

    def ping(self):
        raise FailException("异常测试")
        # return {"ping": "pong"}

    def debug(self, app_id: uuid.UUID):
        """聊天接口"""
        # 1. 获取输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 创建prompt与记忆
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是一个聊天机器人，请根据用户输入回复信息"),
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

        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(memory.load_memory_variables)
                | itemgetter("history")
            )
            | prompt
            | llm
            | StrOutputParser()
        )

        chain_input = {"query": request.json["query"]}
        content = chain.invoke(chain_input)
        memory.save_context(chain_input, {"output": content})

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
