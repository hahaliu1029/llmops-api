import pytest

from app.http.app import app


@pytest.fixture
def client():
    """A test client for the app."""
    app.config["TESTING"] = True  # 设置测试模式
    with app.test_client() as client:  # 创建测试客户端
        yield client  # 运行测试
