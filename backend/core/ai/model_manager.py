import os

from core.system.logs import (
    log_info,
    log_error
)

from core.ai.groq import (
    criar_cliente as criar_cliente_groq,
    enviar_mensagem as enviar_mensagem_groq
)

from core.ai.ollama import (
    criar_cliente as criar_cliente_ollama,
    enviar_mensagem as enviar_mensagem_ollama,
    enviar_mensagem_stream as enviar_mensagem_stream_ollama,
    esta_disponivel as ollama_disponivel
)


MODELO_GROQ = "groq"
MODELO_OLLAMA = "ollama"

MODO_AUTO = "auto"


_model_mode = MODO_AUTO


def obter_modo():

    return _model_mode


def definir_modo(modo):

    global _model_mode

    modo = str(
        modo
    ).strip().lower()


    if modo not in [
        MODO_AUTO,
        MODELO_GROQ,
        MODELO_OLLAMA
    ]:

        raise ValueError(
            "Modo de modelo inválido. "
            "Use: auto, groq ou ollama."
        )


    _model_mode = modo


    log_info(
        f"Modo de IA alterado para: {modo}"
    )


    return _model_mode


def obter_modelo():

    if _model_mode == MODELO_GROQ:

        return MODELO_GROQ


    if _model_mode == MODELO_OLLAMA:

        return MODELO_OLLAMA


    if _groq_configurada():

        return MODELO_GROQ


    return MODELO_OLLAMA


def _groq_configurada():

    return bool(
        os.getenv(
            "GROQ_API_KEY"
        )
    )


def _groq_disponivel():

    return _groq_configurada()


def _ollama_disponivel():

    return ollama_disponivel()


def enviar_mensagem(
    messages,
    temperature=None,
    max_tokens=None
):

    modelo = obter_modelo()


    if modelo == MODELO_OLLAMA:

        log_info(
            "Enviando mensagem através do Ollama."
        )


        return enviar_mensagem_ollama(
            criar_cliente_ollama(),
            messages
        )


    if modelo == MODELO_GROQ:

        log_info(
            "Enviando mensagem através da Groq."
        )


        try:

            return enviar_mensagem_groq(

                criar_cliente_groq(),

                messages,

                temperature=temperature,

                max_tokens=max_tokens

            )


        except Exception as erro:

            log_error(
                f"Erro na Groq: {erro}"
            )


            if _model_mode != MODO_AUTO:

                raise


            log_info(
                "Groq indisponível. "
                "Tentando Ollama como fallback."
            )


            return enviar_mensagem_ollama(
                criar_cliente_ollama(),
                messages
            )


    raise Exception(
        "Nenhum provedor de IA válido foi selecionado."
    )


def enviar_mensagem_stream(
    messages,
    temperature=None,
    max_tokens=None
):

    modelo = obter_modelo()


    if modelo == MODELO_OLLAMA:

        log_info(
            "Iniciando streaming através do Ollama."
        )


        try:

            for parte in enviar_mensagem_stream_ollama(
                criar_cliente_ollama(),
                messages
            ):

                yield parte


            return


        except Exception as erro:

            log_error(
                f"Erro no streaming do Ollama: "
                f"{erro}"
            )


            raise


    if modelo == MODELO_GROQ:

        log_info(
            "Streaming real não está configurado "
            "para a Groq. Usando resposta completa."
        )


        try:

            resposta = enviar_mensagem_groq(

                criar_cliente_groq(),

                messages,

                temperature=temperature,

                max_tokens=max_tokens

            )


        except Exception as erro:

            log_error(
                f"Erro na Groq durante streaming: "
                f"{erro}"
            )


            if _model_mode != MODO_AUTO:

                raise


            log_info(
                "Groq indisponível. "
                "Usando streaming através do Ollama."
            )


            for parte in enviar_mensagem_stream_ollama(
                criar_cliente_ollama(),
                messages
            ):

                yield parte


            return


        if resposta:

            yield resposta


        return


    raise Exception(
        "Nenhum provedor de IA válido foi selecionado."
    )


def esta_disponivel(modo):

    modo = str(
        modo
    ).strip().lower()


    if modo == MODELO_GROQ:

        return _groq_disponivel()


    if modo == MODELO_OLLAMA:

        return _ollama_disponivel()


    if modo == MODO_AUTO:

        return (
            _groq_disponivel()
            or
            _ollama_disponivel()
        )


    return False


def obter_status():

    return {

        "mode":
            obter_modo(),

        "model":
            obter_modelo(),

        "available": {

            MODELO_GROQ:
                esta_disponivel(
                    MODELO_GROQ
                ),

            MODELO_OLLAMA:
                esta_disponivel(
                    MODELO_OLLAMA
                )

        }

    }