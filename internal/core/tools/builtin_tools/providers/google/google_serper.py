from langchain_core.tools import BaseTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools import GoogleSerperRun
from pydantic import BaseModel, Field
from internal.lib.helper import add_attribute


class GoogleSerperArgsSchema(BaseModel):
    """Google SERP 搜索参数描述"""

    query: str = Field(description="需要检索查询的语句")


@add_attribute("args_schema", GoogleSerperArgsSchema)
def google_serper(**kwargs) -> BaseTool:
    """Google SERP 搜索"""
    return GoogleSerperRun(
        name="google_serper",
        description="这是一个低成本的谷歌搜索API。当你需要搜索实事的时候，可以使用该工具，该工具的输入是一个查询语句",
        args_schema=GoogleSerperArgsSchema,
        api_wrapper=GoogleSerperAPIWrapper(),
    )
