import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from pydantic import BaseModel, Field


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


dotenv.load_dotenv(override=True)

google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一个低成本的谷歌搜索API。"
        "当你需要回答有关时事的问题时，可以调用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)

print(google_serper.invoke("InManage最新版本更新了什么?"))
