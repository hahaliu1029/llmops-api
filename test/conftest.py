import pytest

from app.http.app import app as _app
from internal.extension.database_extension import db as _db
from sqlalchemy.orm import sessionmaker, scoped_session


@pytest.fixture
def app():
    """获取Flask应用"""
    _app.config["TESTING"] = True  # 设置测试模式
    return _app


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:  # 创建测试客户端
        yield client  # 运行测试


@pytest.fixture
def db(app):
    """创建一个临时的数据库回话，当测试结束的时候会滚整个事务，从而实现测试与数据实际隔离"""
    with app.app_context():
        # 获取数据库连接并创建事务
        connection = _db.engine.connect()
        transaction = connection.begin()

        # 创建一个临时的数据库会话
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)  # 创建一个线程安全的会话

        # 将数据库会话绑定到当前应用上下文
        _db.session = session

        yield _db

        # 回退数据库并关闭连接，随后清除会话
        transaction.rollback()
        connection.close()
        session.remove()
