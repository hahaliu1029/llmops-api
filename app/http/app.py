import dotenv
from injector import Injector
from flask_migrate import Migrate

from internal.handler.app_handler import AppHandler
from internal.server import Http
from internal.router import Router
from config import Config
from pkg.sqlalchemy import SQLAlchemy
from .module import ExtentionModule

dotenv.load_dotenv()  # 加载环境变量

conf = Config()


injector = Injector([ExtentionModule])

app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router),
)

if __name__ == "__main__":
    app.run(debug=True)
