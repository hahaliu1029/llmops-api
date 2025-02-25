import json
from operator import itemgetter
from queue import Queue
import os
from threading import Thread
from typing import Any, Dict, Generator, Literal
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
    compact_generate_response,
)
from internal.exception import FailException
from internal.service import (
    AppService,
    VectorDatabaseService,
    ConversationService,
    EmbeddingsService,
)
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
from internal.service import ApiToolService
from internal.task.demo_task import demo_task
from internal.core.tools.builtin_tools.providers import BuiltInProviderManager
from langgraph.graph import MessagesState
from langchain_core.messages import ToolMessage
from langgraph.constants import END
from langgraph.graph import StateGraph


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService
    vector_database_service: VectorDatabaseService
    api_tool_service: ApiToolService
    builtin_provider_manager: BuiltInProviderManager
    embeddings_service: EmbeddingsService
    conversation_service: ConversationService

    def create_app(self):
        """创建应用"""
        app = self.app_service.create_app()
        return success_message(f"创建应用成功，应用ID为{app.id}")

    def ping(self):
        human_message = "js是世界上最强大的编程语言"
        # ai_message = """
        #     你好，aa！我是Grok 3，由xAI创建。我是一个AI助手，旨在帮助回答你的问题、提供信息或者只是聊聊天。你今天过得怎么样？有什么特别的事情想聊聊吗？"""
        # old_summary = "人类询问AI关于LLM和Agent的概念。AI解释了LLM（大型语言模型）是一种通过大量文本数据训练出来的智能系统，能够理解和生成自然语言，擅长处理文字相关的任务。Agent（智能代理）则是LLM的升级版，不仅能够回答问题，还能执行搜索信息、分析数据等自动化任务，具有更强的行动能力。AI进一步说明，LLM是语言能力的核心，而Agent则将这种能力与行动力结合，使其更加实用"
        # summary = self.conversation_service.summary(human_message, ai_message, old_summary)
        questions = self.conversation_service.generate_suggested_questions(
            human_message
        )
        return success_json({"questions": questions})
        # providers = self.provider_factory.get_provider_entities()
        # return success_json()
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
        """应用会话调试聊天接口，该接口为流式事件输出"""
        # 1. 获取输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2. 创建队列并提取query数据
        q = Queue()
        query = req.query.data

        # 3. 创建graph图程序应用
        def graph_app() -> None:
            """创建Graph图程序应用并执行"""
            # 创建tools工具列表
            tools = [
                self.builtin_provider_manager.get_tool("google", "google_serper")(),
                self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
                self.builtin_provider_manager.get_tool("gaodeip", "gaode_ip")(),
                self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
                self.builtin_provider_manager.get_tool("time", "current_time")(),
                # self.builtin_provider_manager.get_tool(
                #     "duckduckgo", "duckduckgo_search"
                # )(),
                # self.builtin_provider_manager.get_tool(
                #     "wikipedia", "wikipedia_search"
                # )(),
            ]

            # 定义大语言模型/聊天机器人节点
            def chatbot(state: MessagesState) -> MessagesState:
                """聊天机器人节点"""
                # 创建LLM大语言模型
                llm = ChatOpenAI(
                    model="moonshot-v1-8k",
                    temperature=0.7,
                    openai_api_key=os.getenv("KIMI_API_KEY"),
                    openai_api_base=os.getenv("KIMI_API_BASE"),
                ).bind_tools(tools)

                # 调用stream()函数获取流式输出内容，并判断生成内容是文本还是工具调用参数
                is_first_chunk = True
                is_tool_call = False
                gathered = None
                id = str(uuid.uuid4())
                for chunk in llm.stream(state["messages"]):
                    # 检测是不是第一个块，部分LLM的第一个块不会生成内容，需要抛弃
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue

                    # 叠加相应的区块
                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered += chunk

                    # 判断是否是工具调用参数,往队列中添加不同的数据
                    if chunk.tool_calls or is_tool_call:
                        is_tool_call = True
                        q.put(
                            {
                                "id": id,
                                "event": "agent_thought",
                                "data": json.dumps(chunk.tool_call_chunks),
                            }
                        )
                    else:
                        q.put(
                            {
                                "id": id,
                                "event": "agent_message",
                                "data": chunk.content,
                            }
                        )

                return {
                    "messages": [gathered],
                }

            # 定义工具/函数调用节点
            def tool_executor(state: MessagesState) -> MessagesState:
                """工具执行节点"""
                # 提取数据状态中的tool_calls
                tool_calls = state["messages"][-1].tool_calls

                # 将工具列表转换为字典便于使用
                tools_by_name = {tool.name: tool for tool in tools}

                # 执行工具并得到对应结果
                messages = []
                for tool_call in tool_calls:
                    id = str(uuid.uuid4())
                    tool = tools_by_name[tool_call["name"]]
                    tool_result = tool.invoke(tool_call["args"])
                    messages.append(
                        ToolMessage(
                            tool_call_id=tool_call["id"],
                            content=json.dumps(tool_result),
                            name=tool_call["name"],
                        )
                    )
                    q.put(
                        {
                            "id": id,
                            "event": "agent_action",
                            "data": json.dumps(tool_result),
                        }
                    )

                return {
                    "messages": messages,
                }

            # 定义路由函数
            def route(state: MessagesState) -> Literal["tool_executor", "__end__"]:
                """定义路由节点，用于确认下一步步骤"""
                ai_message = state["messages"][-1]
                if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                    return "tool_executor"
                return END

            # 创建Graph图程序
            graph_builder = StateGraph(MessagesState)

            # 添加节点
            graph_builder.add_node("llm", chatbot)
            graph_builder.add_node("tool_executor", tool_executor)

            # 添加边
            graph_builder.set_entry_point("llm")
            graph_builder.add_conditional_edges("llm", route)
            graph_builder.add_edge("tool_executor", "llm")

            # 编译图程序为可运行组件
            graph = graph_builder.compile()

            # 调用图结构程序并获取结果
            result = graph.invoke({"messages": [("human", query)]})
            print("最终结果：", result)
            q.put(None)

        def stream_event_response() -> Generator:
            """流式事件响应"""
            # 从队列中获取数据并使用yield抛出
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"event: {item.get('event')}\ndata: {json.dumps(item)}\n\n"
                q.task_done()

        # 4. 创建线程并执行
        t = Thread(target=graph_app)
        t.start()

        # 5. 返回流式事件响应
        return compact_generate_response(stream_event_response())

    def _debug(self, app_id: uuid.UUID):
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
