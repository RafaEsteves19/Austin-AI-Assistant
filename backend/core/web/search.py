from tavily import TavilyClient
import os


def criar_cliente_busca():

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise Exception(
            "TAVILY_API_KEY não encontrada no arquivo .env"
        )

    return TavilyClient(
        api_key=api_key
    )


def pesquisar_web(client, pergunta):

    resposta = client.search(
        query=pergunta,
        search_depth="basic",
        max_results=3
    )


    resultados = []


    for item in resposta["results"]:

        resultados.append(
            f"""
Título: {item['title']}

Conteúdo:
{item['content']}
"""
        )


    return "\n".join(resultados)