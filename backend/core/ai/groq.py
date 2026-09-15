from groq import Groq
import os
import time


from core.ai.api_manager import (
    aguardar_limite,
    registrar_consumo_real
)


from core.system.logs import (
    log_info,
    log_error
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

MAX_TENTATIVAS_429 = 3


# ============================================================
# ORDEM DE PRIORIDADE
# ============================================================

MODELOS_PREFERIDOS = [

    "openai/gpt-oss-120b",

    "qwen/qwen3.6-27b",

    "openai/gpt-oss-20b",

    "openai/gpt-oss-safeguard-20b",

    "groq/compound",

    "groq/compound-mini"

]


# ============================================================
# MODELOS QUE NÃO DEVEM PARTICIPAR
# ============================================================

MODELOS_EXCLUIDOS = [

    # Áudio

    "whisper-large-v3",

    "whisper-large-v3-turbo",


    # Áudio / voz

    "canopylabs/orpheus-v1-english",

    "canopylabs/orpheus-arabic-saudi",


    # Segurança / classificação

    "meta-llama/llama-prompt-guard-2-22m",

    "meta-llama/llama-prompt-guard-2-86m"

]


# ============================================================
# CLIENTE
# ============================================================

def criar_cliente():

    api_key = os.getenv(
        "GROQ_API_KEY"
    )


    if not api_key:

        raise Exception(
            "GROQ_API_KEY não encontrada "
            "no arquivo .env"
        )


    return Groq(
        api_key=api_key
    )


# ============================================================
# MODELOS DISPONÍVEIS
# ============================================================

def _obter_modelos_disponiveis(
    client
):

    try:

        modelos = client.models.list()


        disponiveis = []


        for modelo in modelos.data:

            model_id = modelo.id


            if model_id in MODELOS_EXCLUIDOS:

                continue


            if model_id in MODELOS_PREFERIDOS:

                disponiveis.append(
                    model_id
                )


        log_info(

            "Modelos Groq disponíveis: "
            +
            ", ".join(
                disponiveis
            )

        )


        return disponiveis


    except Exception as erro:

        log_error(

            "Não foi possível obter "
            "os modelos da Groq: "
            f"{erro}"

        )


        return []


# ============================================================
# ORDENAR MODELOS
# ============================================================

def _ordenar_modelos(
    modelos_disponiveis
):

    modelos = []


    for modelo in MODELOS_PREFERIDOS:

        if modelo in modelos_disponiveis:

            modelos.append(
                modelo
            )


    return modelos


# ============================================================
# IDENTIFICAR ERRO DE MODELO
# ============================================================

def _erro_modelo_nao_encontrado(
    mensagem
):

    mensagem = mensagem.lower()


    return (

        "404" in mensagem

        or

        "model_not_found" in mensagem

        or

        "does not exist" in mensagem

        or

        "do not have access" in mensagem

    )


# ============================================================
# IDENTIFICAR ERRO DE PERMISSÃO
# ============================================================

def _erro_permissao(
    mensagem
):

    mensagem = mensagem.lower()


    return (

        "403" in mensagem

        or

        "permissions_error" in mensagem

        or

        "model_permission_blocked" in mensagem

        or

        "blocked at the organization level"
        in mensagem

        or

        "blocked at the project level"
        in mensagem

    )


# ============================================================
# IDENTIFICAR RATE LIMIT
# ============================================================

def _erro_limite(
    mensagem
):

    mensagem = mensagem.lower()


    return (

        "429" in mensagem

        or

        "rate limit" in mensagem

        or

        "too many requests" in mensagem

    )


# ============================================================
# OBTER CONTEÚDO
# ============================================================

def _obter_conteudo(
    resposta
):

    if not resposta:

        return None


    if not resposta.choices:

        return None


    mensagem = (

        resposta
        .choices[0]
        .message

    )


    if not mensagem:

        return None


    conteudo = (
        mensagem.content
    )


    if not conteudo:

        return None


    return conteudo


# ============================================================
# EXECUTAR UM MODELO
# ============================================================

def _executar_modelo(
    client,
    modelo,
    messages,
    temperature=None,
    max_tokens=None
):

    tentativa = 1


    while (

        tentativa
        <=
        MAX_TENTATIVAS_429

    ):

        try:

            tokens_estimados = (
                aguardar_limite(
                    modelo,
                    messages
                )
            )


            parametros = {

                "model":
                    modelo,

                "messages":
                    messages

            }


            if temperature is not None:

                parametros[
                    "temperature"
                ] = temperature


            if max_tokens is not None:

                parametros[
                    "max_tokens"
                ] = max_tokens

            else:

                parametros[
                    "max_tokens"
                ] = 1024


            log_info(

                "Enviando mensagem através "
                "da Groq usando o modelo: "
                f"{modelo}"

            )


            resposta = (

                client
                .chat
                .completions
                .create(
                    **parametros
                )

            )


            if resposta.usage:

                registrar_consumo_real(

                    modelo,

                    resposta
                    .usage
                    .total_tokens,

                    tokens_estimados

                )


            conteudo = _obter_conteudo(
                resposta
            )


            if not conteudo:

                raise Exception(

                    f"O modelo {modelo} "
                    "não retornou conteúdo."

                )


            log_info(

                "Resposta obtida através "
                "da Groq usando: "
                f"{modelo}"

            )


            return conteudo


        except Exception as erro:

            mensagem_erro = str(
                erro
            )


            log_error(

                "Erro na API Groq "
                f"({modelo}): "
                f"{mensagem_erro}"

            )


            # ------------------------------------------------
            # MODELO INEXISTENTE
            # ------------------------------------------------

            if _erro_modelo_nao_encontrado(
                mensagem_erro
            ):

                log_info(

                    f"Modelo {modelo} "
                    "não encontrado. "
                    "Passando para o próximo."

                )


                return None


            # ------------------------------------------------
            # PERMISSÃO
            # ------------------------------------------------

            if _erro_permissao(
                mensagem_erro
            ):

                log_info(

                    f"Modelo {modelo} "
                    "sem permissão. "
                    "Passando para o próximo."

                )


                return None


            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if _erro_limite(
                mensagem_erro
            ):

                if (

                    tentativa
                    >=
                    MAX_TENTATIVAS_429

                ):

                    log_info(

                        f"Limite persistente "
                        f"no modelo {modelo}. "
                        "Passando para o próximo."

                    )


                    return None


                espera = (
                    tentativa
                    * 15
                )


                log_info(

                    f"Limite atingido no "
                    f"modelo {modelo}. "
                    f"Aguardando "
                    f"{espera} segundos."

                )


                time.sleep(
                    espera
                )


                tentativa += 1


                continue


            # ------------------------------------------------
            # ERRO NORMAL
            # ------------------------------------------------

            log_info(

                f"Falha no modelo "
                f"{modelo}. "
                "Passando para o próximo."

            )


            return None


    return None


# ============================================================
# ENVIAR MENSAGEM
# ============================================================

def enviar_mensagem(
    client,
    messages,
    temperature=None,
    max_tokens=None
):

    modelos_disponiveis = (

        _obter_modelos_disponiveis(
            client
        )

    )


    modelos = _ordenar_modelos(
        modelos_disponiveis
    )


    if not modelos:

        raise Exception(

            "Nenhum modelo de texto "
            "compatível da Groq está disponível."

        )


    for modelo in modelos:

        resposta = _executar_modelo(

            client,

            modelo,

            messages,

            temperature,

            max_tokens

        )


        if resposta is not None:

            return resposta


        log_info(

            f"Modelo {modelo} falhou "
            "após as tentativas permitidas. "
            "Passando para o próximo."

        )


    raise Exception(

        "Todos os modelos de texto "
        "da Groq falharam."

    )