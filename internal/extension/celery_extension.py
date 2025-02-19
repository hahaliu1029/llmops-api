from flask import Flask
from celery import Task, Celery


def init_app(app: Flask):
    """Celery配置服务初始化"""

    class FlaskTask(Task):
        """定义FlaskTask, 确保任务中可以使用Flask上下文， 这样可以访问flask的配置"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 创建Celery应用并配置
    celery_app = Celery(
        app.name,
        task_cls=FlaskTask,
    )
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    # 将Celery应用绑定到Flask应用
    app.extensions["celery"] = celery_app
