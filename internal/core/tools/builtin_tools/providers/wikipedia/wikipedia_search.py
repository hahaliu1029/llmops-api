from langchain_community.tools import WikipediaQueryRun
from langchain_core.tools import BaseTool
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper


def wikipedia_search(**kwargs) -> BaseTool:
    """获取维基百科搜索结果的工具"""
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
