import os
from flask import request, jsonify
from openai import OpenAI

from internal.schema.app_schema import CompletionReq
from pkg.response import success_json, validate_error_json
from internal.exception import FailException


class AppHandler:
    """应用控制器"""

    def ping(self):
        raise FailException("异常测试")
        # return {"ping": "pong"}

    def completion(self):
        """聊天接口"""
        # 1. 获取输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        print(request.json)
        # 2. 构建DEEPSEEK客户端，调用接口
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE"),
        )
        # 3. 得到结果，返回
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个聊天机器人，请根据用户输入回复信息",
                },
                {"role": "user", "content": request.json["query"]},
            ],
            stream=False,
        )
        content = response.choices[0].message.content

        return success_json({"content": content})
