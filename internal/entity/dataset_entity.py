from enum import Enum

DEFAULT_DATASET_DESCRIPTION_FORMATTER = (
    "当你需要回答关于《{name}》的时候可以引用该知识库"
)


class ProcessType(str, Enum):
    """文档处理规则类型枚举"""

    AUTOMATIC = "automatic"
    CUSTOM = "custom"


# 默认处理规则
DEFAULT_PROCESS_RULE = {
    "mode": "custom",
    "rule": {
        "pre_process_rules": [
            {
                "id": "remove_extra_space",
                "enabled": True,
            },
            {
                "id": "remove_url_and_email",
                "enabled": True,
            },
        ],
        "segment": {
            "separators": [
                "\n\n",
                "\n",
                "。|！|？",
                "\.\s|\!\s|\?\s",  # 英文标点符号后面通常需要加空格
                "；|;\s",
                "，|,\s",
                " ",
                "",
            ],
            "chunk_size": 500,
            "chunk_overlap": 50,
        },
    },
}


class DocumentStatus(str, Enum):
    """文档状态枚举"""

    WAITING = "waiting"
    PARSING = "parsing"
    SPLITTING = "splitting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


class SegmentStatus(str, Enum):
    """分段状态枚举"""

    WAITING = "waiting"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


class RetrievalStrategy(str, Enum):
    """检索策略枚举"""

    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class RetrievalSource(str, Enum):
    """检索来源枚举"""

    HIT_TESTING = "hit_testing"
    APP = "app"
