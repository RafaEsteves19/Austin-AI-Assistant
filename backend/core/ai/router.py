from core.system.logs import (
    log_info
)

from core.ai.model_manager import (
    enviar_mensagem
)


def precisa_pesquisa(
    texto
):

    messages = [

        {
            "role": "system",

            "content": """
Você decide se uma pergunta precisa de pesquisa na internet.

Responda apenas "sim" ou "não".

Pesquise quando a pergunta precisar de:

- informações atuais ou recentes
- notícias
- preços, cotações, clima
- eventos recentes
- versões atuais de software
- fatos que mudam com o tempo

Não pesquise quando:

- a pergunta for sobre conceitos, definições ou programação teórica
- for matemática simples
- for opinião ou conversa casual
- for conhecimento estável ou histórico

Em caso de dúvida, responda "não".
"""
        },

        {
            "role": "user",

            "content": texto
        }

    ]


    resposta = enviar_mensagem(
        messages
    )


    decisao = (
        resposta
        .strip()
        .lower()
    )


    resultado = (
        decisao.startswith("sim")
    )


    if resultado:

        log_info(
            "Pesquisa na internet necessária."
        )

    else:

        log_info(
            "Pesquisa na internet não necessária."
        )


    return resultado