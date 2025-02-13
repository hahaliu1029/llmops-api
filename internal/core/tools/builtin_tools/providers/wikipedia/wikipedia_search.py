from langchain_community.tools.wikipedia.tool import (
    WikipediaQueryRun,
    WikipediaQueryInput,
)
from langchain_core.tools import BaseTool
from langchain_community.utilities.wikipedia import (
    WikipediaAPIWrapper,
)
from internal.lib.helper import add_attribute


@add_attribute("args_schema", WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """获取维基百科搜索结果的工具"""
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
