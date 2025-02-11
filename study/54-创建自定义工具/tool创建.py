from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool


class CalculatorInput(BaseModel):
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool("multiply_tool", args_schema=CalculatorInput, return_direct=True)
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


# 打印下该工具的相关信息
print("名称: ", multiply.name)
print("描述: ", multiply.description)
print("参数: ", multiply.args)
print("直接返回: ", multiply.return_direct)

# 调用工具
print(multiply.invoke({"a": 2, "b": 8}))
