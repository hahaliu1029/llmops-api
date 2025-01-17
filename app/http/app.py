import dotenv
from injector import Binder, Injector
from flask_sqlalchemy import SQLAlchemy

from internal.handler.app_handler import AppHandler
from internal.server import Http
from internal.router import Router
from config import Config
from .module import ExtentionModule

dotenv.load_dotenv()  # 加载环境变量


# def configure(binder: Binder):
#     binder.bind(AppHandler, to=AppHandler)


conf = Config()


injector = Injector([ExtentionModule])

app = Http(
    __name__, conf=conf, db=injector.get(SQLAlchemy), router=injector.get(Router)
)

if __name__ == "__main__":
    app.run(debug=True)
