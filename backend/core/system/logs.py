import redis
from datetime import datetime


REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

REDIS_LOG_KEY = "austin:logs"

# Tempo máximo que os logs podem permanecer no Redis
# caso o sistema não consiga executar o encerramento normal.
LOG_TTL = 3600


cliente_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def limpar_logs():

    cliente_redis.delete(
        REDIS_LOG_KEY
    )


def escrever_log(
    tipo,
    mensagem
):

    horario = datetime.now().strftime(
        "%H:%M:%S"
    )

    texto = (
        f"[{horario}] "
        f"[{tipo}] "
        f"{mensagem}"
    )

    cliente_redis.rpush(
        REDIS_LOG_KEY,
        texto
    )

    # Renova o TTL a cada novo log.
    # Enquanto o Austin estiver ativo, os logs continuam disponíveis.
    cliente_redis.expire(
        REDIS_LOG_KEY,
        LOG_TTL
    )


def log_info(
    mensagem
):

    escrever_log(
        "LOG",
        mensagem
    )


def log_error(
    mensagem
):

    escrever_log(
        "ERRO",
        mensagem
    )