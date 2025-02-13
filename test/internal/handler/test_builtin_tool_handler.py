import pytest

from pkg.response import HttpCode


class TestBuiltinToolHandler:
    """内置工具处理器测试类"""

    def test_get_categories(self, client):
        """测试获取所有工具信息"""
        resp = client.get("/builtin-tools/categories")
        assert resp.status_code == 200
        assert resp.json["code"] == HttpCode.SUCCESS
        assert resp.json["data"] is not None
        assert len(resp.json["data"]) > 0
        print(resp.json)

    def test_get_builtin_tools(self, client):
        """测试获取所有工具信息"""
        resp = client.get("/builtin-tools")
        assert resp.status_code == 200
        assert resp.json["code"] == HttpCode.SUCCESS
        assert resp.json["data"] is not None
        assert len(resp.json["data"]) > 0
        print(resp.json)

    @pytest.mark.parametrize(
        "provider_name, tool_name",
        [
            ("google", "google_serper"),
            ("test", "test"),
        ],
    )
    def test_get_provider_tool(self, provider_name, tool_name, client):
        """测试获取工具信息"""
        resp = client.get(f"/builtin-tools/{provider_name}/tools/{tool_name}")
        assert resp.status_code == 200
        if provider_name == "google" and tool_name == "google_serper":
            assert resp.json["code"] == HttpCode.SUCCESS
            assert resp.json["data"] is not None
            assert resp.json["data"]["name"] == tool_name
        else:
            assert resp.json["code"] == HttpCode.NOT_FOUND
        print(resp.json)

    @pytest.mark.parametrize(
        "provider_name",
        [
            "google",
            "test",
        ],
    )
    def test_get_provider_icon(self, provider_name, client):
        """测试获取工具图标"""
        resp = client.get(f"/builtin-tools/{provider_name}/icon")
        assert resp.status_code == 200
        if provider_name == "test":
            assert resp.json["code"] == HttpCode.NOT_FOUND
        print(resp.json)
