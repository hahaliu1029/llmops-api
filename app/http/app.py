import dotenv
from injector import Injector

from internal.server import Http
from internal.router import Router
from config import Config

dotenv.load_dotenv()  # 加载环境变量

injector = Injector()

conf = Config()

app = Http(__name__, conf=conf, router=injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)
