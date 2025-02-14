import pytest
from pkg.response import HttpCode

openapi_schema_str = """{
  "description": "这是一个查询对应英文单词字典的工具",
  "server": "https://dict.youdao.com",
  "paths": {
    "/suggest": {
      "get": {
        "description": "根据传递的单词查询其字典信息",
        "operationId": "YoudaoSuggest",
        "parameters": [
          {
            "name": "q",
            "in": "query",
            "description": "要检索查询的单词，例如love/computer",
            "required": true,
            "type": "str"
          },
          {
            "name": "doctype",
            "in": "query",
            "description": "返回的数据类型，支持json和xml两种格式，默认情况下json数据",
            "required": false,
            "type": "str"
          }
        ]
      }
    }
  }
}"""


class TestApiToolHandler:
    """自定义API插件处理器测试"""

    @pytest.mark.parametrize(
        "openapi_schema",
        ["123", openapi_schema_str],
    )
    def test_validate_openapi_schema(self, openapi_schema, client):
        """测试校验传递的openapi_schema字符串是否正确"""
        resp = client.post(
            "/api-tools/validate-openapi-schema",
            json={"openapi_schema": openapi_schema},
        )
        assert resp.status_code == 200
        if openapi_schema == "123":
            assert resp.json["code"] == HttpCode.VALIDATE_ERROR
        elif openapi_schema == openapi_schema_str:
            assert resp.json["code"] == HttpCode.SUCCESS

    def test_delete_api_tool_provider(self, client, db):
        """测试根据传递的provider_id删除API工具提供者"""
        provider_id = "134f413c-ac9e-4738-b5cd-2ca6a0f10fd2"
        resp = client.post(f"/api-tools/{provider_id}/delete")
        assert resp.status_code == 200
        assert resp.json["code"] == HttpCode.SUCCESS

        from internal.model import ApiToolProvider

        assert db.session.query(ApiToolProvider).get(provider_id) is None
