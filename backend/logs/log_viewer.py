import time

import redis


REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

REDIS_LOG_KEY = "austin:logs"


cliente_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def acompanhar_logs():

    tamanho_atual = cliente_redis.llen(
        REDIS_LOG_KEY
    )


    while True:

        tamanho_novo = cliente_redis.llen(
            REDIS_LOG_KEY
        )


        if tamanho_novo > tamanho_atual:

            novas_linhas = cliente_redis.lrange(
                REDIS_LOG_KEY,
                tamanho_atual,
                tamanho_novo - 1
            )


            for linha in novas_linhas:

                print(
                    linha,
                    flush=True
                )


            tamanho_atual = tamanho_novo


        elif tamanho_novo < tamanho_atual:

            tamanho_atual = tamanho_novo


        time.sleep(
            0.2
        )


if __name__ == "__main__":

    print(
        "=== Austin Log Viewer ===\n"
    )

    acompanhar_logs()