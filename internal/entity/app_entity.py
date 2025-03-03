from enum import Enum


class AppStatus(str, Enum):
    """应用状态枚举类"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布


class AppConfigType(str, Enum):
    """应用配置类型枚举类"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布


# 应用默认配置信息
DEFAULT_APP_CONFIG = {
    "model_config": {
        "provider": "openai",  # 模型提供商
        "model": "gpt-4o-mini",  # 模型名称
        "parameters": {
            "temperature": 0.5,  # 温度
            "top_p": 0.85,  # top-p
            "frequency_penalty": 0.2,  # 频率惩罚
            "presence_penalty": 0.2,  # 存在惩罚
            "max_tokens": 8192,  # 最大token数
        },
    },
    "dialog_round": 3,  # 对话轮数
    "preset_prompt": "",  # 预设对话
    "tools": [],  # 工具
    "workflows": [],  # 工作流
    "datasets": [],  # 知识库
    "retrieval_config": {  # 检索配置
        "retrieval_strategy": "semantic",  # 检索策略
        "k": 10,  # top-k
        "score": 0.5,  # 分数
    },
    "long_term_memory": {  # 长期记忆
        "enable": False,  # 是否启用
    },
    "opening_statement": "",  # 开场白
    "opening_questions": [],  # 开场问题
    "speech_to_text": {  # 语音转文本
        "enable": False,  # 是否启用
    },
    "text_to_speech": {  # 文本转语音
        "enable": False,  # 是否启用
        "voice": "echo",  # 语音
        "auto_play": False,  # 自动播放
    },
    "review_config": {  # 审核配置
        "enable": False,  # 是否启用
        "keywords": [],  # 关键词
        "inputs_config": {  # 输入配置
            "enable": False,  # 是否启用
            "preset_response": "",  # 预设回复
        },
        "outputs_config": {  # 输出配置
            "enable": False,  # 是否启用
        },
    },
}
