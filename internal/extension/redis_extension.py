import redis
from flask import Flask
from redis.connection import Connection, SSLConnection

# redis客户端
redis_client = redis.Redis()


def init_app(app: Flask):
    """初始化Redis"""
    # 检测不同场景使用不同的连接方式
    connection_class = Connection
    if app.config.get("REDIS_USE_SSL", False):
        connection_class = SSLConnection

    # 创建redis连接池
    redis_client.connection_pool = redis.ConnectionPool(
        **{
            "host": app.config.get("REDIS_HOST", "127.0.0.1"),
            "port": app.config.get("REDIS_PORT", 6379),
            "db": app.config.get("REDIS_DB", 0),
            "password": app.config.get("REDIS_PASSWORD", None),
            "username": app.config.get("REDIS_USERNAME", None),
            "encoding": "utf-8",
            "encoding_errors": "strict",
            "decode_responses": False,
        },
        connection_class=connection_class
    )

    app.extensions["redis"] = redis_client
