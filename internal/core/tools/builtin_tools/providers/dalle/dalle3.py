from langchain_community.tools.openai_dalle_image_generation import (
    OpenAIDALLEImageGenerationTool,
)
from langchain_core.tools import BaseTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from pydantic import BaseModel, Field


class Dalle3ArgsSchema(BaseModel):
    query: str = Field(description="输入应该是生成图像的文本提示(prompt)。")


def dalle3(**kwargs) -> BaseTool:
    """返回dalle3绘图的工具"""
    return OpenAIDALLEImageGenerationTool(
        api_wrapper=DallEAPIWrapper(**kwargs),
        args_schema=Dalle3ArgsSchema,
    )
