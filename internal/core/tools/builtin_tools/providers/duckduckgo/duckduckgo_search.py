from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class DDGInput(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


def duckduckgo_search(**kwargs) -> BaseTool:
    """返回一个 DuckDuckGo 搜索工具"""
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索引擎，当你需要搜索实事时，可以使用它。工具的输入是一个查询语句",
        args_schema=DDGInput,
    )
