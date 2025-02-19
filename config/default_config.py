# 应用默认配置

DEFAULT_CONFIG = {
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",
    "WTF_CSRF_ENABLED": "False",
    # Redis配置
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": 6379,
    "REDIS_DB": "0",
    "REDIS_PASSWORD": "",
    "REDIS_USERNAME": "",
    "REDIS_USE_SSL": "False",
    # Celery默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_BACKEND_DB": 1,
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 3600,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",
}
