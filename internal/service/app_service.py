import json
from dataclasses import dataclass
from datetime import datetime
from threading import Thread
from typing import Any, Generator
from uuid import UUID
import uuid

from datetime import datetime
from flask import request, current_app, Flask
from injector import inject
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from redis import Redis
from sqlalchemy import func, desc

from internal.core.agent.agents import FunctionCallAgent, AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.memory import TokenBufferMemory
from internal.core.tools.api_tools.entities import ToolEntity

from internal.core.tools.api_tools.providers import ApiProvidersManager
from internal.core.tools.builtin_tools.providers import BuiltInProviderManager
from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.exception import (
    NotFoundException,
    ForbiddenException,
    ValidateErrorException,
    FailException,
)
from internal.lib.helper import datetime_to_timestamp
from internal.model import (
    App,
    Account,
    AppConfigVersion,
    ApiTool,
    Dataset,
    AppConfig,
    AppDatasetJoin,
    Conversation,
    Message,
    MessageAgentThought,
)
from internal.schema.app_schema import (
    CreateAppReq,
    GetPublishHistoriesWithPageReq,
    GetDebugConversationMessagesWithPageReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .conversation_service import ConversationService
from .retrieval_service import RetrievalService


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""

    db: SQLAlchemy
    redis_client: Redis
    conversation_service: ConversationService
    retrieval_service: RetrievalService
    api_provider_manager: ApiProvidersManager
    builtin_provider_manager: BuiltInProviderManager

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """创建Agent应用服务"""
        # 1.开启数据库自动提交上下文
        now = datetime.now()
        with self.db.auto_commit():
            # 2.创建应用记录，并刷新数据，从而可以拿到应用id
            app = App(
                id=uuid.uuid4(),
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
                updated_at=now,  # 显式设置更新时间
                created_at=now,  # 显式设置创建时间
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """根据传递的id获取应用的基础信息"""
        # 1.查询数据库获取应用基础信息
        app = self.get(App, app_id)

        # 2.判断应用是否存在
        if not app:
            raise NotFoundException("该应用不存在，请核实后重试")

        # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后尝试")

        return app

    def get_draft_app_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        """根据传递的应用id，获取指定的应用草稿配置信息"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.提取应用的草稿配置
        draft_app_config = app.draft_app_config

        # todo:3.校验model_config配置信息，等待多LLM实现的时候再来完成

        # 4.循环遍历工具列表删除已经被删除的工具信息
        draft_tools = draft_app_config.tools
        validate_tools = []
        tools = []
        for draft_tool in draft_tools:
            if draft_tool["type"] == "builtin_tool":
                # 5.查询内置工具提供者，并检测是否存在
                provider = self.builtin_provider_manager.get_provider(
                    draft_tool["provider_id"]
                )
                if not provider:
                    continue

                # 6.获取提供者下的工具实体，并检测是否存在
                tool_entity = provider.get_tool_entity(draft_tool["tool_id"])
                if not tool_entity:
                    continue

                # 7.判断工具的params和草稿中的params是否一致，如果不一致则全部重置为默认值（或者考虑删除这个工具的引用）
                param_keys = set([param.name for param in tool_entity.params])
                params = draft_tool["params"]
                if set(draft_tool["params"].keys()) - param_keys:
                    params = {
                        param.name: param.default
                        for param in tool_entity.params
                        if param.default is not None
                    }

                # 8.数据都存在，并且参数已经校验完毕，可以将数据添加到validate_tools
                validate_tools.append({**draft_tool, "params": params})

                # 9.组装内置工具展示信息
                provider_entity = provider.provider_entity
                tools.append(
                    {
                        "type": "builtin_tool",
                        "provider": {
                            "id": provider_entity.name,
                            "name": provider_entity.name,
                            "label": provider_entity.label,
                            "icon": f"{request.scheme}://{request.host}/builtin-tools/{provider_entity.name}/icon",
                            "description": provider_entity.description,
                        },
                        "tool": {
                            "id": tool_entity.name,
                            "name": tool_entity.name,
                            "label": tool_entity.label,
                            "description": tool_entity.description,
                            "params": draft_tool["params"],
                        },
                    }
                )
            elif draft_tool["type"] == "api_tool":
                # 10.查询数据库获取对应的工具记录，并检测是否存在
                tool_record = (
                    self.db.session.query(ApiTool)
                    .filter(
                        ApiTool.provider_id == draft_tool["provider_id"],
                        ApiTool.name == draft_tool["tool_id"],
                    )
                    .one_or_none()
                )
                if not tool_record:
                    continue

                # 11.数据校验通过，往validate_tools中添加数据
                validate_tools.append(draft_tool)

                # 12.组装api工具展示信息
                provider = tool_record.provider
                tools.append(
                    {
                        "type": "api_tool",
                        "provider": {
                            "id": str(provider.id),
                            "name": provider.name,
                            "label": provider.name,
                            "icon": provider.icon,
                            "description": provider.description,
                        },
                        "tool": {
                            "id": str(tool_record.id),
                            "name": tool_record.name,
                            "label": tool_record.name,
                            "description": tool_record.description,
                            "params": {},
                        },
                    }
                )

        # 13.判断是否需要更新草稿配置中的工具列表信息
        if draft_tools != validate_tools:
            # 14.更新草稿配置中的工具列表
            self.update(draft_app_config, tools=validate_tools)

        # 15.校验知识库列表，如果引用了不存在/被删除的知识库，需要剔除数据并更新，同时获取知识库的额外信息
        datasets = []
        draft_datasets = draft_app_config.datasets
        dataset_records = (
            self.db.session.query(Dataset).filter(Dataset.id.in_(draft_datasets)).all()
        )
        dataset_dict = {
            str(dataset_record.id): dataset_record for dataset_record in dataset_records
        }
        dataset_sets = set(dataset_dict.keys())

        # 16.计算存在的知识库id列表，为了保留原始顺序，使用列表循环的方式来判断
        exist_dataset_ids = [
            dataset_id for dataset_id in draft_datasets if dataset_id in dataset_sets
        ]

        # 17.判断是否存在已删除的知识库，如果存在则更新
        if set(exist_dataset_ids) != set(draft_datasets):
            self.update(draft_app_config, datasets=exist_dataset_ids)

        # 18.循环获取知识库数据
        for dataset_id in exist_dataset_ids:
            dataset = dataset_dict.get(str(dataset_id))
            datasets.append(
                {
                    "id": str(dataset.id),
                    "name": dataset.name,
                    "icon": dataset.icon,
                    "description": dataset.description,
                }
            )

        # todo:19.校验工作流列表对应的数据
        workflows = []

        # 20.将数据转换成字典后返回
        return {
            "id": str(draft_app_config.id),
            "model_config": draft_app_config.model_config,
            "dialog_round": draft_app_config.dialog_round,
            "preset_prompt": draft_app_config.preset_prompt,
            "tools": tools,
            "workflows": workflows,
            "datasets": datasets,
            "retrieval_config": draft_app_config.retrieval_config,
            "long_term_memory": draft_app_config.long_term_memory,
            "opening_statement": draft_app_config.opening_statement,
            "opening_questions": draft_app_config.opening_questions,
            "speech_to_text": draft_app_config.speech_to_text,
            "text_to_speech": draft_app_config.text_to_speech,
            "review_config": draft_app_config.review_config,
            "updated_at": datetime_to_timestamp(draft_app_config.updated_at),
            "created_at": datetime_to_timestamp(draft_app_config.created_at),
        }

    def update_draft_app_config(
        self,
        app_id: UUID,
        draft_app_config: dict[str, Any],
        account: Account,
    ) -> AppConfigVersion:
        """根据传递的应用id+草稿配置修改指定应用的最新草稿"""
        # 1.获取应用信息并校验
        app = self.get_app(app_id, account)

        # 2.校验传递的草稿配置信息
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)

        # 3.获取当前应用的最新草稿信息
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            # todo:由于目前使用server_onupdate，所以该字段暂时需要手动传递
            updated_at=datetime.now(),
            **draft_app_config,
        )

        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，发布/更新指定的应用草稿配置为运行时配置"""
        # 1.获取应用的信息以及草稿信息
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 2.创建应用运行配置（在这里暂时不删除历史的运行配置）
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=draft_app_config["model_config"],
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],
            # todo:工作流模块完成后该处可能有变动
            workflows=draft_app_config["workflows"],
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            review_config=draft_app_config["review_config"],
        )

        # 3.更新应用关联的运行时配置以及状态
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 4.先删除原有的知识库关联记录
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        # 5.新增新的知识库关联记录
        for dataset in draft_app_config["datasets"]:
            self.create(AppDatasetJoin, app_id=app_id, dataset_id=dataset["id"])

        # 6.获取应用草稿记录，并移除id、version、config_type、updated_at、created_at字段
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields = [
            "id",
            "version",
            "config_type",
            "updated_at",
            "created_at",
            "_sa_instance_state",
        ]
        for field in remove_fields:
            draft_app_config_copy.pop(field)

        # 7.获取当前最大的发布版本
        max_version = (
            self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0))
            .filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            )
            .scalar()
        )

        # 8.新增发布历史配置
        self.create(
            AppConfigVersion,
            version=max_version + 1,
            config_type=AppConfigType.PUBLISHED,
            **draft_app_config_copy,
        )

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，取消发布指定的应用配置"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.检测下当前应用的状态是否为已发布
        if app.status != AppStatus.PUBLISHED:
            raise FailException("当前应用未发布，请核实后重试")

        # 3.修改账号的发布状态，并清空关联配置id
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 4.删除应用关联的知识库信息
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        return app

    def get_publish_histories_with_page(
        self, app_id: UUID, req: GetPublishHistoriesWithPageReq, account: Account
    ) -> tuple[list[AppConfigVersion], Paginator]:
        """根据传递的应用id+请求数据，获取指定应用的发布历史配置列表信息"""
        # 1.获取应用信息并校验权限
        self.get_app(app_id, account)

        # 2.构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 3.执行分页并获取数据
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion)
            .filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            )
            .order_by(desc("version"))
        )

        return app_config_versions, paginator

    def fallback_history_to_draft(
        self,
        app_id: UUID,
        app_config_version_id: UUID,
        account: Account,
    ) -> AppConfigVersion:
        """根据传递的应用id、历史配置版本id、账号信息，回退特定配置到草稿"""
        # 1.校验应用权限并获取信息
        app = self.get_app(app_id, account)

        # 2.查询指定的历史版本配置id
        app_config_version = self.get(AppConfigVersion, app_config_version_id)
        if not app_config_version:
            raise NotFoundException("该历史版本配置不存在，请核实后重试")

        # 3.校验历史版本配置信息（剔除已删除的工具、知识库、工作流）
        draft_app_config_dict = app_config_version.__dict__.copy()
        remove_fields = [
            "id",
            "app_id",
            "version",
            "config_type",
            "updated_at",
            "created_at",
            "_sa_instance_state",
        ]
        for field in remove_fields:
            draft_app_config_dict.pop(field)

        # 4.校验历史版本配置信息
        draft_app_config_dict = self._validate_draft_app_config(
            draft_app_config_dict, account
        )

        # 5.更新草稿配置信息
        draft_app_config_record = app.draft_app_config
        self.update(
            draft_app_config_record,
            # todo:更新时间补丁信息
            updated_at=datetime.now(),
            **draft_app_config_dict,
        )

        return draft_app_config_record

    def get_debug_conversation_summary(self, app_id: UUID, account: Account) -> str:
        """根据传递的应用id+账号获取指定应用的调试会话长期记忆"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.获取应用的草稿配置，并校验长期记忆是否启用
        draft_app_config = self.get_draft_app_config(app_id, account)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用并未开启长期记忆，无法获取")

        return app.debug_conversation.summary

    def update_debug_conversation_summary(
        self, app_id: UUID, summary: str, account: Account
    ) -> Conversation:
        """根据传递的应用id+总结更新指定应用的调试长期记忆"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.获取应用的草稿配置，并校验长期记忆是否启用
        draft_app_config = self.get_draft_app_config(app_id, account)
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用并未开启长期记忆，无法获取")

        # 3.更新应用长期记忆
        debug_conversation = app.debug_conversation
        self.update(debug_conversation, summary=summary)

        return debug_conversation

    def delete_debug_conversation(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id，删除指定的应用调试会话"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.判断是否存在debug_conversation_id这个数据，如果不存在表示没有会话，无需执行任何操作
        if not app.debug_conversation_id:
            return app

        # 3.否则将debug_conversation_id的值重置为None
        self.update(app, debug_conversation_id=None)

        return app

    def debug_chat(self, app_id: UUID, query: str, account: Account) -> Generator:
        """根据传递的应用id+提问query向特定的应用发起会话调试"""
        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 2.获取应用的最新草稿配置信息
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 3.获取当前应用的调试会话信息
        debug_conversation = app.debug_conversation

        # 4.新建一条消息记录
        message = self.create(
            Message,
            app_id=app_id,
            conversation_id=debug_conversation.id,
            created_by=account.id,
            query=query,
            status=MessageStatus.NORMAL,
        )

        # todo:5.根据传递的model_config实例化不同的LLM模型，等待多LLM接入后该处会发生变化
        llm = ChatOpenAI(
            model=draft_app_config["model_config"]["model"],
            **draft_app_config["model_config"]["parameters"],
        )

        # 6.实例化TokenBufferMemory用于提取短期记忆
        token_buffer_memory = TokenBufferMemory(
            db=self.db,
            conversation=debug_conversation,
            model_instance=llm,
        )
        history = token_buffer_memory.get_history_prompt_messages(
            message_limit=draft_app_config["dialog_round"],
        )

        # 7.将草稿配置中的tools转换成LangChain工具
        tools = []
        for tool in draft_app_config["tools"]:
            # 8.根据不同的工具类型执行不同的操作
            if tool["type"] == "builtin_tool":
                # 9.内置工具，通过builtin_provider_manager获取工具实例
                builtin_tool = self.builtin_provider_manager.get_tool(
                    tool["provider"]["id"], tool["tool"]["name"]
                )
                if not builtin_tool:
                    continue
                tools.append(builtin_tool(**tool["tool"]["params"]))
            else:
                # 10.API工具，首先根据id找到ApiTool记录，然后创建示例
                api_tool = self.get(ApiTool, tool["tool"]["id"])
                if not api_tool:
                    continue
                tools.append(
                    self.api_provider_manager.get_tool(
                        ToolEntity(
                            id=str(api_tool.id),
                            name=api_tool.name,
                            url=api_tool.url,
                            method=api_tool.method,
                            description=api_tool.description,
                            headers=api_tool.provider.headers,
                            parameters=api_tool.parameters,
                        )
                    )
                )

        # 11.检测是否关联了知识库
        if draft_app_config["datasets"]:
            # 12.构建LangChain知识库检索工具
            dataset_retrieval = (
                self.retrieval_service.create_langchain_tool_from_search(
                    flask_app=current_app._get_current_object(),
                    dataset_ids=[
                        dataset["id"] for dataset in draft_app_config["datasets"]
                    ],
                    account_id=account.id,
                    retrival_source=RetrievalSource.APP,
                    **draft_app_config["retrieval_config"],
                )
            )
            tools.append(dataset_retrieval)

        # todo:13.构建Agent智能体，目前暂时使用FunctionCallAgent
        agent = FunctionCallAgent(
            llm=llm,
            agent_config=AgentConfig(
                user_id=account.id,
                invoke_from=InvokeFrom.DEBUGGER,
                enable_long_term_memory=draft_app_config["long_term_memory"]["enable"],
                tools=tools,
                review_config=draft_app_config["review_config"],
            ),
        )

        agent_thoughts = {}
        for agent_thought in agent.stream(
            {
                "messages": [HumanMessage(query)],
                "history": history,
                "long_term_memory": debug_conversation.summary,
            }
        ):
            # 15.提取thought以及answer
            event_id = str(agent_thought.id)

            # 17.将数据填充到agent_thought，便于存储到数据库服务中
            if agent_thought.event != QueueEvent.PING:
                # 18.除了agent_message数据为叠加，其他均为覆盖
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    if event_id not in agent_thoughts:
                        # 19.初始化智能体消息事件
                        agent_thoughts[event_id] = {
                            "id": event_id,
                            "task_id": str(agent_thought.task_id),
                            "event": agent_thought.event,
                            "thought": agent_thought.thought,
                            "observation": agent_thought.observation,
                            "tool": agent_thought.tool,
                            "tool_input": agent_thought.tool_input,
                            "message": agent_thought.message,
                            "answer": agent_thought.answer,
                            "latency": agent_thought.latency,
                        }
                    else:
                        # 20.叠加智能体消息
                        agent_thoughts[event_id] = {
                            **agent_thoughts[event_id],
                            "thought": agent_thoughts[event_id]["thought"]
                            + agent_thought.thought,
                            "answer": agent_thoughts[event_id]["answer"]
                            + agent_thought.answer,
                            "latency": agent_thought.latency,
                        }
                else:
                    # 21.处理其他类型事件的消息
                    agent_thoughts[event_id] = {
                        "id": event_id,
                        "task_id": str(agent_thought.task_id),
                        "event": agent_thought.event,
                        "thought": agent_thought.thought,
                        "observation": agent_thought.observation,
                        "tool": agent_thought.tool,
                        "tool_input": agent_thought.tool_input,
                        "message": agent_thought.message,
                        "answer": agent_thought.answer,
                        "latency": agent_thought.latency,
                    }

            data = {
                "id": event_id,
                "conversation_id": str(debug_conversation.id),
                "message_id": str(message.id),
                "task_id": str(agent_thought.task_id),
                "event": agent_thought.event,
                "thought": agent_thought.thought,
                "observation": agent_thought.observation,
                "tool": agent_thought.tool,
                "tool_input": agent_thought.tool_input,
                "answer": agent_thought.answer,
                "latency": agent_thought.latency,
            }
            yield f"event: {agent_thought.event}\ndata:{json.dumps(data)}\n\n"

        # 22.将消息以及推理过程添加到数据库
        thread = Thread(
            target=self._save_agent_thoughts,
            kwargs={
                "flask_app": current_app._get_current_object(),
                "account_id": account.id,
                "app_id": app_id,
                "draft_app_config": draft_app_config,
                "conversation_id": debug_conversation.id,
                "message_id": message.id,
                "agent_thoughts": agent_thoughts,
            },
        )
        thread.start()

    def stop_debug_chat(self, app_id: UUID, task_id: UUID, account: Account) -> None:
        """根据传递的应用id+任务id+账号，停止某个应用的调试会话，中断流式事件"""
        # 1.获取应用信息并校验权限
        self.get_app(app_id, account)

        # 2.调用智能体队列管理器停止特定任务
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.DEBUGGER, account.id)

    # def get_debug_conversation_messages_with_page(
    #     self,
    #     app_id: UUID,
    #     req: GetDebugConversationMessagesWithPageReq,
    #     account: Account,
    # ) -> tuple[list[Message], Paginator]:
    #     """根据传递的应用id+请求数据，获取调试会话消息列表分页数据"""
    #     # 1.获取应用信息并校验权限
    #     app = self.get_app(app_id, account)

    #     # 2.获取应用的调试会话
    #     debug_conversation = app.debug_conversation

    #     # 3.构建分页器并构建游标条件
    #     paginator = Paginator(db=self.db, req=req)
    #     filters = []
    #     if req.created_at.data:
    #         # 4.将时间戳转换成DateTime
    #         created_at_datetime = datetime.fromtimestamp(req.created_at.data)
    #         filters.append(Message.created_at <= created_at_datetime)

    #     # 5.执行分页并查询数据
    #     messages = paginator.paginate(
    #         self.db.session.query(Message)
    #         .filter(
    #             Message.conversation_id == debug_conversation.id,
    #             Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
    #             Message.answer != "",
    #             *filters,
    #         )
    #         .order_by(desc("created_at"))
    #     )

    #     return messages, paginator

    def _save_agent_thoughts(
        self,
        flask_app: Flask,
        account_id: UUID,
        app_id: UUID,
        draft_app_config: dict[str, Any],
        conversation_id: UUID,
        message_id: UUID,
        agent_thoughts: dict[str, Any],
    ) -> None:
        """存储智能体推理步骤信息"""
        with flask_app.app_context():
            # 1.定义变量存储推理位置及总耗时
            position = 0
            latency = 0

            # 2.在子线程中重新查询conversation以及message，确保对象会被子线程的会话管理到
            conversation = self.get(Conversation, conversation_id)
            message = self.get(Message, message_id)

            # 3.循环遍历所有的智能体推理过程执行存储操作
            for key, item in agent_thoughts.items():
                # 4.存储长期记忆召回、推理、消息、动作、知识库检索等步骤
                if item["event"] in [
                    QueueEvent.LONG_TERM_MEMORY_RECALL,
                    QueueEvent.AGENT_THOUGHT,
                    QueueEvent.AGENT_MESSAGE,
                    QueueEvent.AGENT_ACTION,
                    QueueEvent.DATASET_RETRIEVAL,
                ]:
                    # 5.更新位置及总耗时
                    position += 1
                    latency += item["latency"]

                    # 6.创建智能体消息推理步骤
                    self.create(
                        MessageAgentThought,
                        app_id=app_id,
                        conversation_id=conversation.id,
                        message_id=message.id,
                        invoke_from=InvokeFrom.DEBUGGER,
                        created_by=account_id,
                        position=position,
                        event=item["event"],
                        thought=item["thought"],
                        observation=item["observation"],
                        tool=item["tool"],
                        tool_input=item["tool_input"],
                        message=item["message"],
                        answer=item["answer"],
                        latency=item["latency"],
                    )

                # 7.检测事件是否为Agent_message
                if item["event"] == QueueEvent.AGENT_MESSAGE:
                    # 8.更新消息信息
                    self.update(
                        message,
                        message=item["message"],
                        answer=item["answer"],
                        latency=latency,
                    )

                    # 9.检测是否开启长期记忆
                    if draft_app_config["long_term_memory"]["enable"]:
                        new_summary = self.conversation_service.summary(
                            message.query, item["answer"], conversation.summary
                        )
                        self.update(
                            conversation,
                            summary=new_summary,
                        )

                    # 10.处理生成新会话名称
                    if conversation.is_new:
                        new_conversation_name = (
                            self.conversation_service.generate_conversation_name(
                                message.query
                            )
                        )
                        self.update(
                            conversation,
                            name=new_conversation_name,
                        )

                # 11.判断是否为停止或者错误，如果是则需要更新消息状态
                if item["event"] in [QueueEvent.STOP, QueueEvent.ERROR]:
                    self.update(
                        message,
                        status=(
                            MessageStatus.STOP
                            if item["event"] == QueueEvent.STOP
                            else MessageStatus.ERROR
                        ),
                        observation=item["observation"],
                    )
                    break

    def _validate_draft_app_config(
        self, draft_app_config: dict[str, Any], account: Account
    ) -> dict[str, Any]:
        """校验传递的应用草稿配置信息，返回校验后的数据"""
        # 1.校验上传的草稿配置中对应的字段，至少拥有一个可以更新的配置
        acceptable_fields = [
            "model_config",
            "dialog_round",
            "preset_prompt",
            "tools",
            "workflows",
            "datasets",
            "retrieval_config",
            "long_term_memory",
            "opening_statement",
            "opening_questions",
            "speech_to_text",
            "text_to_speech",
            "review_config",
        ]

        # 2.判断传递的草稿配置是否在可接受字段内
        if (
            not draft_app_config
            or not isinstance(draft_app_config, dict)
            or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidateErrorException("草稿配置字段出错，请核实后重试")

        # todo:3.校验model_config字段，等待多LLM接入时完成该步骤校验

        # 4.校验dialog_round上下文轮数，校验数据类型以及范围
        if "dialog_round" in draft_app_config:
            dialog_round = draft_app_config["dialog_round"]
            if not isinstance(dialog_round, int) or not (0 <= dialog_round <= 100):
                raise ValidateErrorException("携带上下文轮数范围为0-100")

        # 5.校验preset_prompt
        if "preset_prompt" in draft_app_config:
            preset_prompt = draft_app_config["preset_prompt"]
            if not isinstance(preset_prompt, str) or len(preset_prompt) > 2000:
                raise ValidateErrorException(
                    "人设与回复逻辑必须是字符串，长度在0-2000个字符"
                )

        # 6.校验tools工具
        if "tools" in draft_app_config:
            tools = draft_app_config["tools"]
            validate_tools = []

            # 6.1 tools类型必须为列表，空列表则代表不绑定任何工具
            if not isinstance(tools, list):
                raise ValidateErrorException("工具列表必须是列表型数据")
            # 6.2 tools的长度不能超过5
            if len(tools) > 5:
                raise ValidateErrorException("Agent绑定的工具数不能超过5")
            # 6.3 循环校验工具里的每一个参数
            for tool in tools:
                # 6.4 校验tool非空并且类型为字典
                if not tool or not isinstance(tool, dict):
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.5 校验工具的参数是不是type、provider_id、tool_id、params
                if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.6 校验type类型是否为builtin_tool以及api_tool
                if tool["type"] not in ["builtin_tool", "api_tool"]:
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.7 校验provider_id和tool_id
                if (
                    not tool["provider_id"]
                    or not tool["tool_id"]
                    or not isinstance(tool["provider_id"], str)
                    or not isinstance(tool["tool_id"], str)
                ):
                    raise ValidateErrorException("插件提供者或者插件标识参数出错")
                # 6.8 校验params参数，类型为字典
                if not isinstance(tool["params"], dict):
                    raise ValidateErrorException("插件自定义参数格式错误")
                # 6.9 校验对应的工具是否存在，而且需要划分成builtin_tool和api_tool
                if tool["type"] == "builtin_tool":
                    builtin_tool = self.builtin_provider_manager.get_tool(
                        tool["provider_id"], tool["tool_id"]
                    )
                    if not builtin_tool:
                        continue
                else:
                    api_tool = (
                        self.db.session.query(ApiTool)
                        .filter(
                            ApiTool.provider_id == tool["provider_id"],
                            ApiTool.name == tool["tool_id"],
                            ApiTool.account_id == account.id,
                        )
                        .one_or_none()
                    )
                    if not api_tool:
                        continue

                validate_tools.append(tool)

            # 6.10 校验绑定的工具是否重复
            check_tools = [
                f"{tool['provider_id']}_{tool['tool_id']}" for tool in validate_tools
            ]
            if len(set(check_tools)) != len(validate_tools):
                raise ValidateErrorException("绑定插件存在重复")

            # 6.11 重新赋值工具
            draft_app_config["tools"] = validate_tools

        # todo:7.校验workflows，等待工作流模块完成后实现
        if "workflows" in draft_app_config:
            draft_app_config["workflows"] = []

        # 8.校验datasets知识库列表
        if "datasets" in draft_app_config:
            datasets = draft_app_config["datasets"]

            # 8.1 判断datasets类型是否为列表
            if not isinstance(datasets, list):
                raise ValidateErrorException("绑定知识库列表参数格式错误")
            # 8.2 判断关联的知识库列表是否超过5个
            if len(datasets) > 5:
                raise ValidateErrorException("Agent绑定的知识库数量不能超过5个")
            # 8.3 循环校验知识库的每个参数
            for dataset_id in datasets:
                try:
                    UUID(dataset_id)
                except Exception as e:
                    raise ValidateErrorException("知识库列表参数必须是UUID")
            # 8.4 判断是否传递了重复的知识库
            if len(set(datasets)) != len(datasets):
                raise ValidateErrorException("绑定知识库存在重复")
            # 8.5 校验绑定的知识库权限，剔除不属于当前账号的知识库
            dataset_records = (
                self.db.session.query(Dataset)
                .filter(
                    Dataset.id.in_(datasets),
                    Dataset.account_id == account.id,
                )
                .all()
            )
            dataset_sets = set(
                [str(dataset_record.id) for dataset_record in dataset_records]
            )
            draft_app_config["datasets"] = [
                dataset_id for dataset_id in datasets if dataset_id in dataset_sets
            ]

        # 9.校验retrieval_config检索配置
        if "retrieval_config" in draft_app_config:
            retrieval_config = draft_app_config["retrieval_config"]

            # 9.1 判断检索配置非空且类型为字典
            if not retrieval_config or not isinstance(retrieval_config, dict):
                raise ValidateErrorException("检索配置格式错误")
            # 9.2 校验检索配置的字段类型
            if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
                raise ValidateErrorException("检索配置格式错误")
            # 9.3 校验检索策略是否正确
            if retrieval_config["retrieval_strategy"] not in [
                "semantic",
                "full_text",
                "hybrid",
            ]:
                raise ValidateErrorException("检测策略格式错误")
            # 9.4 校验最大召回数量
            if not isinstance(retrieval_config["k"], int) or not (
                0 <= retrieval_config["k"] <= 10
            ):
                raise ValidateErrorException("最大召回数量范围为0-10")
            # 9.5 校验得分/最小匹配度
            if not isinstance(retrieval_config["score"], float) or not (
                0 <= retrieval_config["score"] <= 1
            ):
                raise ValidateErrorException("最小匹配范围为0-1")

        # 10.校验long_term_memory长期记忆配置
        if "long_term_memory" in draft_app_config:
            long_term_memory = draft_app_config["long_term_memory"]

            # 10.1 校验长期记忆格式
            if not long_term_memory or not isinstance(long_term_memory, dict):
                raise ValidateErrorException("长期记忆设置格式错误")
            # 10.2 校验长期记忆属性
            if set(long_term_memory.keys()) != {"enable"} or not isinstance(
                long_term_memory["enable"], bool
            ):
                raise ValidateErrorException("长期记忆设置格式错误")

        # 11.校验opening_statement对话开场白
        if "opening_statement" in draft_app_config:
            opening_statement = draft_app_config["opening_statement"]

            # 11.1 校验对话开场白类型以及长度
            if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
                raise ValidateErrorException("对话开场白的长度范围是0-2000")

        # 12.校验opening_questions开场建议问题列表
        if "opening_questions" in draft_app_config:
            opening_questions = draft_app_config["opening_questions"]

            # 12.1 校验是否为列表，并且长度不超过3
            if not isinstance(opening_questions, list) or len(opening_questions) > 3:
                raise ValidateErrorException("开场建议问题不能超过3个")
            # 12.2 开场建议问题每个元素都是一个字符串
            for opening_question in opening_questions:
                if not isinstance(opening_question, str):
                    raise ValidateErrorException("开场建议问题必须是字符串")

        # 13.校验speech_to_text语音转文本
        if "speech_to_text" in draft_app_config:
            speech_to_text = draft_app_config["speech_to_text"]

            # 13.1 校验语音转文本格式
            if not speech_to_text or not isinstance(speech_to_text, dict):
                raise ValidateErrorException("语音转文本设置格式错误")
            # 13.2 校验语音转文本属性
            if set(speech_to_text.keys()) != {"enable"} or not isinstance(
                speech_to_text["enable"], bool
            ):
                raise ValidateErrorException("语音转文本设置格式错误")

        # 14.校验text_to_speech文本转语音设置
        if "text_to_speech" in draft_app_config:
            text_to_speech = draft_app_config["text_to_speech"]

            # 14.1 校验字典格式
            if not isinstance(text_to_speech, dict):
                raise ValidateErrorException("文本转语音设置格式错误")
            # 14.2 校验字段类型
            if (
                set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                or not isinstance(text_to_speech["enable"], bool)
                # todo:等待多模态Agent实现时添加音色
                or text_to_speech["voice"] not in ["echo"]
                or not isinstance(text_to_speech["auto_play"], bool)
            ):
                raise ValidateErrorException("文本转语音设置格式错误")

        # 15.校验review_config审核配置
        if "review_config" in draft_app_config:
            review_config = draft_app_config["review_config"]

            # 15.1 校验字段格式，非空
            if not review_config or not isinstance(review_config, dict):
                raise ValidateErrorException("审核配置格式错误")
            # 15.2 校验字段信息
            if set(review_config.keys()) != {
                "enable",
                "keywords",
                "inputs_config",
                "outputs_config",
            }:
                raise ValidateErrorException("审核配置格式错误")
            # 15.3 校验enable
            if not isinstance(review_config["enable"], bool):
                raise ValidateErrorException("review.enable格式错误")
            # 15.4 校验keywords
            if (
                not isinstance(review_config["keywords"], list)
                or (review_config["enable"] and len(review_config["keywords"]) == 0)
                or len(review_config["keywords"]) > 100
            ):
                raise ValidateErrorException("review.keywords非空且不能超过100个关键词")
            for keyword in review_config["keywords"]:
                if not isinstance(keyword, str):
                    raise ValidateErrorException("review.keywords敏感词必须是字符串")
            # 15.5 校验inputs_config输入配置
            if (
                not review_config["inputs_config"]
                or not isinstance(review_config["inputs_config"], dict)
                or set(review_config["inputs_config"].keys())
                != {"enable", "preset_response"}
                or not isinstance(review_config["inputs_config"]["enable"], bool)
                or not isinstance(
                    review_config["inputs_config"]["preset_response"], str
                )
            ):
                raise ValidateErrorException("review.inputs_config必须是一个字典")
            # 15.6 校验outputs_config输出配置
            if (
                not review_config["outputs_config"]
                or not isinstance(review_config["outputs_config"], dict)
                or set(review_config["outputs_config"].keys()) != {"enable"}
                or not isinstance(review_config["outputs_config"]["enable"], bool)
            ):
                raise ValidateErrorException("review.outputs_config格式错误")
            # 15.7 在开启审核模块的时候，必须确保inputs_config或者是outputs_config至少有一个是开启的
            if review_config["enable"]:
                if (
                    review_config["inputs_config"]["enable"] is False
                    and review_config["outputs_config"]["enable"] is False
                ):
                    raise ValidateErrorException("输入审核和输出审核至少需要开启一项")

                if (
                    review_config["inputs_config"]["enable"]
                    and review_config["inputs_config"]["preset_response"].strip() == ""
                ):
                    raise ValidateErrorException("输入审核预设响应不能为空")

        return draft_app_config
