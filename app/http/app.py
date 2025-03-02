import dotenv
from flask_migrate import Migrate

from internal.server import Http
from internal.router import Router
from config import Config
from pkg.sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .module import injector
from internal.middleware import Middleware

dotenv.load_dotenv(override=True)  # 加载环境变量

conf = Config()


app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router),
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=True)
