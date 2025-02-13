import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """TestAppHandler class."""

    @pytest.mark.parametrize(
        "app_id, query",
        [
            ("15fd2840-e294-4413-83d0-e083e9a7bc6b", None),
            ("15fd2840-e294-4413-83d0-e083e9a7bc6b", "你好，你是"),
        ],
    )
    def test_completion(self, app_id, query, client):
        resp = client.post(f"/apps/{app_id}/debug", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json["code"] == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json["code"] == HttpCode.SUCCESS
        # assert resp.json["code"] == HttpCode.SUCCESS
        print(resp.json)
