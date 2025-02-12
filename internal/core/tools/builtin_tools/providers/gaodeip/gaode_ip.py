import json
import os
from typing import Any, Type

import requests
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class GaodeIPLookupArgsSchema(BaseModel):
    ip: str = Field(description="需要查询归属地的目标IP地址，例如：8.8.8.8")


class GaodeIPLookupTool(BaseTool):
    """根据传入的IP地址查询归属地"""

    name: str = "gaode_ip_lookup"
    description: str = "用于查询IP归属地信息的工具"
    args_schema: Type[BaseModel] = GaodeIPLookupArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """根据传入的IP地址调用API获取归属地信息"""
        try:
            ip = kwargs.get("ip")
            if not ip:
                return "查询IP归属地的IP地址不能为空"

            # 在 _run 方法中获取 API Key，避免 pydantic 解析问题
            gaode_api_key = os.getenv("GAODE_API_KEY")
            if not gaode_api_key:
                return "GAODE_API_KEY 未配置，请检查环境变量"

            api_url = "https://restapi.amap.com/v3/ip"
            session = requests.session()

            # 请求IP定位信息
            response = session.get(
                api_url,
                params={"key": gaode_api_key, "ip": ip},
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            response.raise_for_status()
            ip_data = response.json()

            if ip_data.get("info") == "OK":
                return json.dumps(ip_data, ensure_ascii=False)

            return f"获取IP {ip} 归属地信息失败"
        except Exception as e:
            return f"获取IP {ip} 归属地信息失败，错误信息: {str(e)}"


def gaode_ip() -> BaseTool:
    """获取一个高德IP查询工具"""
    return GaodeIPLookupTool()
