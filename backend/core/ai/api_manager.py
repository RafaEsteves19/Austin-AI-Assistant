import time
from datetime import datetime

import tiktoken

from core.system.logs import log_info


# ============================================================
# LIMITES POR MODELO
# ============================================================

LIMITES_MODELOS = {

    "openai/gpt-oss-120b": {

        "rpm": 1000,

        "tpm": 250000

    },

    "openai/gpt-oss-20b": {

        "rpm": 1000,

        "tpm": 250000

    },

    "qwen/qwen3.6-27b": {

        "rpm": 1000,

        "tpm": 250000

    },

    "openai/gpt-oss-safeguard-20b": {

        "rpm": 1000,

        "tpm": 150000

    },

    "groq/compound": {

        "rpm": 200,

        "tpm": 200000

    },

    "groq/compound-mini": {

        "rpm": 200,

        "tpm": 200000

    }

}


# ============================================================
# CONFIGURAÇÃO
# ============================================================

MARGEM_SEGURANCA = 5


# ============================================================
# CONTADORES
# ============================================================

contadores = {}


def _criar_contador():

    return {

        "requests":
            0,

        "tokens":
            0,

        "minute_start":
            datetime.now()

    }


def _obter_contador(
    modelo
):

    if modelo not in contadores:

        contadores[
            modelo
        ] = _criar_contador()


    return contadores[
        modelo
    ]


# ============================================================
# TOKENIZAÇÃO
# ============================================================

encoding = tiktoken.get_encoding(
    "cl100k_base"
)


def contar_tokens(
    messages
):

    texto = ""


    for message in messages:

        texto += str(
            message.get(
                "content",
                ""
            )
        )


    tokens = encoding.encode(
        texto
    )


    return len(tokens)


# ============================================================
# RESET
# ============================================================

def resetar_contador(
    modelo
):

    contador = _obter_contador(
        modelo
    )


    agora = datetime.now()


    segundos = (

        agora
        -
        contador[
            "minute_start"
        ]

    ).total_seconds()


    if segundos >= 60:

        contador[
            "requests"
        ] = 0


        contador[
            "tokens"
        ] = 0


        contador[
            "minute_start"
        ] = agora


        log_info(
            "Limite da API renovado | "
            f"Modelo: {modelo}"
        )


# ============================================================
# AGUARDAR LIMITE
# ============================================================

def aguardar_limite(
    modelo,
    messages
):

    if modelo not in LIMITES_MODELOS:

        raise ValueError(

            "Não existe limite configurado "
            f"para o modelo: {modelo}"

        )


    limite = LIMITES_MODELOS[
        modelo
    ]


    contador = _obter_contador(
        modelo
    )


    tokens_estimados = contar_tokens(
        messages
    )


    while True:

        resetar_contador(
            modelo
        )


        pode_enviar = (

            contador[
                "requests"
            ]
            +
            1

            <=

            limite[
                "rpm"
            ]

            and

            contador[
                "tokens"
            ]
            +
            tokens_estimados

            <=

            limite[
                "tpm"
            ]

        )


        if pode_enviar:

            contador[
                "requests"
            ] += 1


            contador[
                "tokens"
            ] += tokens_estimados


            log_info(

                "API liberada | "

                f"Modelo: {modelo} | "

                f"Requests: "
                f"{contador['requests']}"
                f"/{limite['rpm']} | "

                f"Tokens estimados: "
                f"{contador['tokens']}"
                f"/{limite['tpm']}"

            )


            return tokens_estimados


        agora = datetime.now()


        segundos_passados = (

            agora
            -
            contador[
                "minute_start"
            ]

        ).total_seconds()


        espera = max(

            60
            -
            segundos_passados
            +
            MARGEM_SEGURANCA,

            1

        )


        log_info(

            "Limite atingido | "

            f"Modelo: {modelo} | "

            f"Aguardando "
            f"{int(espera)} segundos."

        )


        time.sleep(
            espera
        )


# ============================================================
# CONSUMO REAL
# ============================================================

def registrar_consumo_real(
    modelo,
    tokens_reais,
    tokens_estimados
):

    contador = _obter_contador(
        modelo
    )


    limite = LIMITES_MODELOS.get(
        modelo
    )


    if not limite:

        return


    diferenca = (

        tokens_reais
        -
        tokens_estimados

    )


    contador[
        "tokens"
    ] += diferenca


    contador[
        "tokens"
    ] = max(

        contador[
            "tokens"
        ],

        0

    )


    log_info(

        "Consumo real atualizado | "

        f"Modelo: {modelo} | "

        f"Tokens no minuto: "
        f"{contador['tokens']}"
        f"/{limite['tpm']}"

    )