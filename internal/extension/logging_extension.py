import logging
import os
from flask import Flask
from logging.handlers import TimedRotatingFileHandler


def init_app(app: Flask):
    """日志记录器初始化"""
    # 设置日至存储文件夹如果不存在则创建
    log_folder = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # 定义日志文件名
    log_file = os.path.join(log_folder, "app.log")

    # 设置日志格式，并且每天更新一次
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "[%(asctime)s].%(msecs)03d %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logging.getLogger().addHandler(handler)
    # 开发环境下同时输出到控制台
    if app.debug or os.getenv("FLASK_ENV") == "development":
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
