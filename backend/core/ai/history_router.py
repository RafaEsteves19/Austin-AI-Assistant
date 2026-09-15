from core.system.logs import log_info

from core.ai.model_manager import (
    enviar_mensagem
)


def analisar_historico(texto):

    messages = [

        {
            "role": "system",

            "content": """
Você é um classificador de intenção de histórico.

Responda APENAS:
buscar
abrir
nenhum

BUSCAR:
Use quando o usuário quer recuperar ou consultar
conversas anteriores com o assistente.

Exemplos:
"Você lembra do que conversamos?"
buscar

"Qual foi nossa última conversa?"
buscar

"Você lembra do que falamos sobre React?"
buscar

"Quero encontrar aquela conversa sobre API"
buscar

"Mostre meu histórico"
buscar

ABRIR:
Use quando o usuário quer abrir, analisar ou
continuar uma conversa específica do histórico.

Exemplos:
"Abra a conversa 2"
abrir

"Abra a conversa sobre React"
abrir

"Quero continuar aquela conversa"
abrir

"Me explique o que falamos naquela conversa"
abrir

NENHUM:
Use para qualquer outro assunto.

IMPORTANTE:
"último", "última", "recente" ou "anterior"
não significam histórico por si só.

Se estiverem relacionados a jogos, notícias,
resultados, eventos, datas ou informações externas,
responda "nenhum".

Exemplos:
"Quanto foi o último jogo da Espanha?"
nenhum

"Qual foi a última notícia sobre tecnologia?"
nenhum

"Qual o resultado recente do campeonato?"
nenhum

Somente use buscar ou abrir quando houver
intenção clara de consultar o histórico do
assistente.
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


    resultado = (
        resposta
        .strip()
        .lower()
    )


    if resultado not in [
        "buscar",
        "abrir",
        "nenhum"
    ]:

        resultado = "nenhum"


    if resultado != "nenhum":

        log_info(
            f"Histórico detectado: {resultado}"
        )


    return resultado