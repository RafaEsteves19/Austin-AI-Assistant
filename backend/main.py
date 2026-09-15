import atexit
import uvicorn

from core.system.logs import limpar_logs
from core.system.server import registrar_servidor


def encerrar():

    limpar_logs()


if __name__ == "__main__":

    limpar_logs()

    atexit.register(
        encerrar
    )

    config = uvicorn.Config(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )

    servidor = uvicorn.Server(
        config
    )

    registrar_servidor(
        servidor
    )

    servidor.run()