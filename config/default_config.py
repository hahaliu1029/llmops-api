# 应用默认配置

DEFAULT_CONFIG = {
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,  # 连接池大小
    "SQLALCHEMY_POOL_RECYCLE": 3600,  # 连接池回收时间
    "SQLALCHEMY_ECHO": "True",  # 是否打印SQL语句
    "WTF_CSRF_ENABLED": "False",  # CSRF保护
}
