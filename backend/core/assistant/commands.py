from core.ai.model_manager import (
    enviar_mensagem
)


# Despedidas que podem ser identificadas
# diretamente, sem consultar a IA.
DESPEDIDAS_DIRETAS = {

    "tchau",
    "adeus",
    "até mais",
    "ate mais",
    "até logo",
    "ate logo",
    "até amanhã",
    "ate amanha",
    "boa noite",
    "falou",
    "fui",

    "pode encerrar",
    "pode fechar",
    "pode desligar",

    "encerrar a conversa",
    "terminar a conversa",
    "já terminamos",
    "ja terminamos",

    "isso é tudo",
    "isso e tudo",

    "acabou",

    "por hoje é só",
    "por hoje e so"
}


def _normalizar_texto(texto):

    return (
        texto
        .strip()
        .lower()
    )


def _despedida_direta(texto):

    texto_normalizado = _normalizar_texto(
        texto
    )

    return (
        texto_normalizado
        in DESPEDIDAS_DIRETAS
    )


def deseja_encerrar(texto):

    # Primeiro verificamos despedidas claras
    # sem gastar uma chamada da IA.
    if _despedida_direta(texto):

        return True


    messages = [

        {
            "role": "system",

            "content": """
Você identifica se o usuário deseja encerrar a conversa.

Responda somente:

sim

ou

não

Considere como encerramento quando houver
uma intenção clara de finalizar a conversa.

Exemplos:

- pode encerrar;
- pode fechar;
- pode desligar;
- encerrar a conversa;
- terminar a conversa;
- já terminamos;
- isso é tudo;
- acabou;
- por hoje é só.

Não considere encerramento:

- perguntas sobre comandos de saída;
- perguntas técnicas usando palavras como sair,
  fechar ou encerrar;
- exemplos de código;
- assuntos relacionados à programação;
- qualquer situação em que exista dúvida.

Em caso de dúvida responda "não".
"""
        },

        {
            "role": "user",
            "content": texto
        }

    ]


    resposta = enviar_mensagem(
        messages,
        temperature=0,
        max_tokens=2
    )


    decisao = (
        resposta
        .strip()
        .lower()
    )


    return decisao.startswith(
        "sim"
    )