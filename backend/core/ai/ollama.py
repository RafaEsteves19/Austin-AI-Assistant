import time
import requests

from core.system.logs import (
    log_info,
    log_error
)


OLLAMA_URL = "http://127.0.0.1:11434"

MODELO_OLLAMA = "llama3.2:3b"

MAX_TENTATIVAS = 3


def criar_cliente():

    return {
        "url": OLLAMA_URL,
        "model": MODELO_OLLAMA
    }


def esta_disponivel():

    try:

        resposta = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=2
        )

        return resposta.ok

    except Exception:

        return False


def modelo_disponivel():

    try:

        resposta = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=2
        )

        if not resposta.ok:

            return False

        dados = resposta.json()

        modelos = dados.get(
            "models",
            []
        )

        for modelo in modelos:

            nome = modelo.get(
                "name",
                ""
            )

            if nome == MODELO_OLLAMA:

                return True

        return False

    except Exception:

        return False


def enviar_mensagem(
    client,
    messages
):

    if not esta_disponivel():

        raise Exception(
            "O servidor Ollama não está disponível."
        )


    if not modelo_disponivel():

        raise Exception(
            f"O modelo {MODELO_OLLAMA} "
            "não está instalado no Ollama."
        )


    tentativa = 1


    while tentativa <= MAX_TENTATIVAS:

        try:

            resposta = requests.post(

                f"{OLLAMA_URL}/api/chat",

                json={

                    "model":
                        MODELO_OLLAMA,

                    "messages":
                        messages,

                    "stream":
                        False

                },

                timeout=300
            )


            if not resposta.ok:

                raise Exception(
                    f"Ollama retornou HTTP "
                    f"{resposta.status_code}: "
                    f"{resposta.text}"
                )


            dados = resposta.json()


            mensagem = dados.get(
                "message"
            )


            if not mensagem:

                raise Exception(
                    "O Ollama não retornou "
                    "uma mensagem válida."
                )


            conteudo = mensagem.get(
                "content"
            )


            if not conteudo:

                raise Exception(
                    "O Ollama retornou "
                    "uma resposta vazia."
                )


            log_info(
                "Resposta obtida através do Ollama."
            )


            return conteudo


        except Exception as erro:

            mensagem_erro = str(
                erro
            )


            log_error(
                f"Erro no Ollama: "
                f"{mensagem_erro}"
            )


            if tentativa >= MAX_TENTATIVAS:

                break


            espera = tentativa * 2


            log_info(
                f"Erro temporário no Ollama. "
                f"Tentando novamente em "
                f"{espera} segundos."
            )


            time.sleep(
                espera
            )


            tentativa += 1


    raise Exception(
        "Não foi possível obter resposta "
        "do Ollama após várias tentativas."
    )


def enviar_mensagem_stream(
    client,
    messages
):

    if not esta_disponivel():

        raise Exception(
            "O servidor Ollama não está disponível."
        )


    if not modelo_disponivel():

        raise Exception(
            f"O modelo {MODELO_OLLAMA} "
            "não está instalado no Ollama."
        )


    tentativa = 1


    while tentativa <= MAX_TENTATIVAS:

        try:

            resposta = requests.post(

                f"{OLLAMA_URL}/api/chat",

                json={

                    "model":
                        MODELO_OLLAMA,

                    "messages":
                        messages,

                    "stream":
                        True

                },

                stream=True,

                timeout=300
            )


            if not resposta.ok:

                raise Exception(
                    f"Ollama retornou HTTP "
                    f"{resposta.status_code}: "
                    f"{resposta.text}"
                )


            log_info(
                "Streaming iniciado através do Ollama."
            )


            encontrou_conteudo = False


            for linha in resposta.iter_lines(
                decode_unicode=True
            ):

                if not linha:

                    continue


                import json


                dados = json.loads(
                    linha
                )


                mensagem = dados.get(
                    "message"
                )


                if mensagem:

                    conteudo = mensagem.get(
                        "content",
                        ""
                    )


                    if conteudo:

                        encontrou_conteudo = True

                        yield conteudo


                if dados.get(
                    "done",
                    False
                ):

                    break


            resposta.close()


            if not encontrou_conteudo:

                raise Exception(
                    "O Ollama não retornou "
                    "conteúdo durante o streaming."
                )


            log_info(
                "Streaming do Ollama finalizado."
            )


            return


        except Exception as erro:

            mensagem_erro = str(
                erro
            )


            log_error(
                f"Erro no streaming do Ollama: "
                f"{mensagem_erro}"
            )


            if tentativa >= MAX_TENTATIVAS:

                break


            espera = tentativa * 2


            log_info(
                f"Erro temporário no streaming "
                f"do Ollama. Tentando novamente "
                f"em {espera} segundos."
            )


            time.sleep(
                espera
            )


            tentativa += 1


    raise Exception(
        "Não foi possível obter o streaming "
        "do Ollama após várias tentativas."
    )