import json
from queue import Queue
import os
from threading import Thread
from typing import Any, Dict, Generator
import uuid
from dataclasses import dataclass
from flask import request
from injector import inject

from internal.entity.conversation_entity import InvokeFrom
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
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.memory import BaseMemory
from langchain_core.tracers.schemas import Run
from internal.service import ApiToolService
from internal.task.demo_task import demo_task
from internal.core.tools.builtin_tools.providers import BuiltInProviderManager
from internal.core.agent.agents import FunctionCallAgent, AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig
from redis import Redis


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
    redis_client: Redis

    def create_app(self):
        """创建应用"""
        app = self.app_service.create_app()
        return success_message(f"创建应用成功，应用ID为{app.id}")

    def ping(self):
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI

        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(
                    model="moonshot-v1-8k",
                    temperature=0.7,
                    openai_api_key=os.getenv("KIMI_API_KEY"),
                    openai_api_base=os.getenv("KIMI_API_BASE"),
                ),
                preset_prompt="你是一个老诗人，请根据用户提供的主题来写一首诗",
            )
        )
        state = agent.run("木匠", history=[], long_term_memory="")
        content = state["messages"][-1].content

        return success_json({"content": content})

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

        query = req.query.data

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

        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(
                    model="deepseek-chat",
                    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
                ),
                enable_long_term_memory=True,
                tools=tools,
            ),
            AgentQueueManager(
                user_id=uuid.uuid4(),
                task_id=uuid.uuid4(),
                invoke_from=InvokeFrom.DEBUGGER,
                redis_client=self.redis_client,
            ),
        )

        def stream_event_response() -> Generator:
            """流式事件响应"""
            for agent_queue_event in agent.run(query, [], "用户介绍自己叫aaa"):
                data = {
                    "id": str(agent_queue_event.id),
                    "task_id": str(agent_queue_event.task_id),
                    "event": agent_queue_event.event,
                    "thought": agent_queue_event.thought,
                    "observation": agent_queue_event.observation,
                    "tool": agent_queue_event.tool,
                    "tool_input": agent_queue_event.tool_input,
                    "answer": agent_queue_event.answer,
                    "latency": agent_queue_event.latency,
                }
                yield f"event: {agent_queue_event.event}\ndata: {json.dumps(data)}\n\n"

        # 5. 返回流式事件响应
        return compact_generate_response(stream_event_response())

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
