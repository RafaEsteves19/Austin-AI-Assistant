from pathlib import Path

import subprocess

from dotenv import load_dotenv

from core.system.logs import (
    log_info,
    log_error,
    limpar_logs
)

from core.system.files import ler_arquivo

from core.system.errors import mensagem_erro

from core.ai.groq import criar_cliente

from core.ai.model_manager import (
    enviar_mensagem,
    enviar_mensagem_stream
)

from core.ai.router import precisa_pesquisa

from core.ai.history_router import analisar_historico

from core.web.search import (
    criar_cliente_busca,
    pesquisar_web
)

from core.assistant.commands import deseja_encerrar

from core.assistant.conversation import (
    criar_conversa,
    adicionar_usuario,
    adicionar_assistente
)

from history.history_manager import (
    iniciar_historico,
    adicionar_mensagem,
    finalizar_historico
)

from history.history_search import (
    buscar_historico,
    selecionar_por_numero,
    existe_selecao_pendente
)

from history.history_context import (
    obter_contexto_historico,
    limpar_contexto_historico
)

from personality.greetings import saudacao_inicial


load_dotenv()


class AustinAssistant:

    def __init__(self):
        self.client = None
        self.search_client = None
        self.messages = []
        self.historico_iniciado = False
        self.awaiting_confirmation = False
        self.awaiting_shutdown_confirmation = False
        self.shutdown_requested = False
        self.state = "idle"

        self._initialize()


    def _initialize(self):
        self.client = criar_cliente()

        self.search_client = criar_cliente_busca()

        instructions = (
            self._carregar_instructions()
        )

        self.messages = criar_conversa(
            instructions
        )


    def _carregar_instructions(self):
        instructions = ler_arquivo(
            "backend/personality/instructions.md"
        )

        preferences = ler_arquivo(
            "database/user/preferences.md"
        )

        return (
            f"{instructions}\n\n"
            "## CONTEXTO DO USUÁRIO\n\n"
            f"{preferences}"
        )


    def status(self):
        return {
            "status": "online",

            "state":
                self.state,

            "awaiting_confirmation":
                self.awaiting_confirmation,

            "awaiting_shutdown_confirmation":
                self.awaiting_shutdown_confirmation,

            "shutdown_requested":
                self.shutdown_requested
        }


    def greeting(self):
        return saudacao_inicial()


    def _resetar_sessao(self):

        # ==================================================
        # FINALIZAR SESSÃO ANTERIOR NO BANCO
        # ==================================================
        if self.historico_iniciado:
            finalizar_historico()

        limpar_contexto_historico()

        self.messages = criar_conversa(
            self._carregar_instructions()
        )

        self.historico_iniciado = False

        self.awaiting_confirmation = False

        self.awaiting_shutdown_confirmation = False

        self.shutdown_requested = False

        self.state = "idle"


    def new_session(self):

        self._resetar_sessao()

        log_info(
            "Nova sessão iniciada."
        )

        return {
            "response":
                self.greeting(),

            "state":
                self.state,

            "requires_confirmation":
                False,

            "session_ended":
                False
        }


    def _executar_shutdown(self):

        try:

            base_dir = (
                Path(__file__)
                .resolve()
                .parents[3]
            )

            shutdown_file = (
                base_dir /
                "shutdown.bat"
            )

            if not shutdown_file.exists():

                log_error(
                    "Arquivo shutdown.bat não encontrado: "
                    f"{shutdown_file}"
                )

                return False

            subprocess.Popen(
                [
                    "cmd",
                    "/c",
                    "start",
                    "",
                    str(shutdown_file)
                ],

                cwd=str(base_dir),

                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                )
            )

            return True

        except Exception as erro:

            log_error(
                f"Erro ao executar shutdown do Austin: "
                f"{erro}"
            )

            return False


    def _confirmation_response(
        self,
        text
    ):

        normalized = (
            text
            .strip()
            .lower()
        )


        # ========================================
        # CONFIRMAÇÃO DE ENCERRAMENTO DA SESSÃO
        # ========================================

        if self.awaiting_confirmation:

            if normalized in (
                "s",
                "sim"
            ):

                self.awaiting_confirmation = False

                # Finaliza a sessão SQLite atual
                if self.historico_iniciado:
                    finalizar_historico()

                limpar_contexto_historico()

                self.messages = criar_conversa(
                    self._carregar_instructions()
                )

                self.historico_iniciado = False

                self.state = "idle"

                # Limpa os logs da sessão encerrada.
                limpar_logs()

                self.awaiting_shutdown_confirmation = True

                return {
                    "response": (
                        "Sessão encerrada. "
                        "Deseja que eu desligue os servidores?"
                    ),

                    "state":
                        "idle",

                    "requires_confirmation":
                        True,

                    "session_ended":
                        False,

                    "shutdown_requested":
                        False
                }


            if normalized in (
                "n",
                "nao",
                "não"
            ):

                self.awaiting_confirmation = False

                self.state = "idle"

                return {
                    "response": (
                        "Certo. "
                        "A sessão continuará ativa."
                    ),

                    "state":
                        "idle",

                    "requires_confirmation":
                        False,

                    "session_ended":
                        False,

                    "shutdown_requested":
                        False
                }


            return {
                "response":
                    "Responda apenas com sim ou não.",

                "state":
                    "idle",

                "requires_confirmation":
                    True,

                "session_ended":
                    False,

                "shutdown_requested":
                    False
            }


        # ========================================
        # CONFIRMAÇÃO DE DESLIGAMENTO
        # ========================================

        if self.awaiting_shutdown_confirmation:

            if normalized in (
                "s",
                "sim"
            ):

                self.awaiting_shutdown_confirmation = False

                self.shutdown_requested = True

                self.state = "shutdown"

                resposta = {
                    "response": (
                        "Entendido. "
                        "Protocolo de desligamento autorizado. "
                        "Encerrando os sistemas."
                    ),

                    "state":
                        "shutdown",

                    "requires_confirmation":
                        False,

                    "session_ended":
                        True,

                    "shutdown_requested":
                        True
                }

                # O frontend recebe primeiro a confirmação.
                #
                # Em seguida iniciamos o processo separado
                # responsável por desligar os componentes
                # do Austin.

                self._executar_shutdown()

                return resposta


            if normalized in (
                "n",
                "nao",
                "não"
            ):

                self.awaiting_shutdown_confirmation = False

                self.shutdown_requested = False

                self.state = "idle"

                return {
                    "response": (
                        "Protocolo de desligamento cancelado. "
                        "Os servidores permanecerão ativos."
                    ),

                    "state":
                        "idle",

                    "requires_confirmation":
                        False,

                    "session_ended":
                        False,

                    "shutdown_requested":
                        False
                }


            return {
                "response":
                    "Responda apenas com sim ou não.",

                "state":
                    "idle",

                "requires_confirmation":
                    True,

                "session_ended":
                    False,

                "shutdown_requested":
                    False
            }


        return None


    def open_history(
        self,
        arquivo
    ):

        from history.history_manager import (
            selecionar_conversa
        )

        selecionar_conversa(
            arquivo
        )

        from history.history_search import (
            resumir_conversa
        )

        resumo = resumir_conversa()

        from history.history_context import (
            adicionar_contexto_historico
        )

        adicionar_contexto_historico(
            resumo
        )

        self.state = "responding"

        return {
            "response":
                resumo,

            "state":
                "responding",

            "requires_confirmation":
                False,

            "session_ended":
                False
        }


    def _preparar_mensagem(
        self,
        pergunta
    ):

        messages_para_envio = (
            self.messages.copy()
        )

        contexto_historico = (
            obter_contexto_historico()
        )

        if contexto_historico:

            messages_para_envio.append({
                "role":
                    "system",

                "content": f"""
O usuário abriu uma conversa anterior.

Use esse contexto para continuar a conversa
quando ele for relevante para a mensagem atual.

Contexto da conversa anterior:

{contexto_historico}

"""
            })


        if precisa_pesquisa(
            pergunta
        ):

            log_info(
                "Pesquisa na internet ativada"
            )

            contexto = pesquisar_web(
                self.search_client,
                pergunta
            )

            messages_para_envio.append({
                "role":
                    "system",

                "content": f"""
Use as informações abaixo como contexto atualizado.

Contexto:

{contexto}

"""
            })

        else:

            log_info(
                "Usando conhecimento interno"
            )


        return messages_para_envio


    def process_message(
        self,
        pergunta
    ):

        pergunta = (
            pergunta
            .strip()
        )


        if not pergunta:

            return {
                "response":
                    "Informe uma mensagem para continuar.",

                "state":
                    "idle",

                "requires_confirmation":
                    False,

                "session_ended":
                    False
            }


        try:

            # ========================================
            # CONFIRMAÇÕES PENDENTES
            # ========================================

            if (
                self.awaiting_confirmation
                or
                self.awaiting_shutdown_confirmation
            ):

                resposta = self._confirmation_response(
                    pergunta
                )

                return resposta


            # ========================================
            # VERIFICAÇÃO DE DESPEDIDA
            # ========================================

            self.state = "thinking"

            if deseja_encerrar(
                pergunta
            ):

                self.awaiting_confirmation = True

                self.state = "idle"

                return {
                    "response":
                        "Deseja encerrar a sessão?",

                    "state":
                        "idle",

                    "requires_confirmation":
                        True,

                    "session_ended":
                        False
                }


            # ========================================
            # SELEÇÃO DE HISTÓRICO
            # ========================================

            if existe_selecao_pendente():

                resposta = selecionar_por_numero(
                    pergunta
                )

                if resposta:

                    self.state = "responding"

                    return {
                        "response":
                            resposta,

                        "state":
                            "responding",

                        "requires_confirmation":
                            False,

                        "session_ended":
                            False
                    }


            # ========================================
            # HISTÓRICO
            # ========================================

            acao_historico = analisar_historico(
                pergunta
            )

            if acao_historico in (
                "buscar",
                "abrir"
            ):

                resposta = buscar_historico(
                    pergunta
                )

                self.state = "responding"

                return {
                    "response":
                        resposta,

                    "state":
                        "responding",

                    "requires_confirmation":
                        False,

                    "session_ended":
                        False
                }


            # ========================================
            # INICIAR SESSÃO NO HISTÓRICO
            # ========================================

            if not self.historico_iniciado:

                iniciar_historico(
                    pergunta
                )

                self.historico_iniciado = True


            adicionar_usuario(
                self.messages,
                pergunta
            )

            adicionar_mensagem(
                "user",
                pergunta
            )


            messages_para_envio = (
                self._preparar_mensagem(
                    pergunta
                )
            )

            self.state = "responding"

            resposta = enviar_mensagem(
                messages_para_envio
            )


            adicionar_assistente(
                self.messages,
                resposta
            )

            adicionar_mensagem(
                "assistant",
                resposta
            )


            self.state = "idle"

            return {
                "response":
                    resposta,

                "state":
                    "idle",

                "requires_confirmation":
                    False,

                "session_ended":
                    False
            }


        except Exception as erro:

            self.state = "error"

            log_error(
                str(erro)
            )

            return {
                "response":
                    mensagem_erro(erro),

                "state":
                    "error",

                "requires_confirmation":
                    False,

                "session_ended":
                    False
            }


    def process_message_stream(
        self,
        pergunta
    ):

        pergunta = (
            pergunta
            .strip()
        )


        if not pergunta:

            yield {
                "type":
                    "done",

                "content":
                    "Informe uma mensagem para continuar.",

                "state":
                    "idle",

                "requires_confirmation":
                    False,

                "session_ended":
                    False
            }

            return


        try:

            # ========================================
            # CONFIRMAÇÕES PENDENTES
            # ========================================

            if (
                self.awaiting_confirmation
                or
                self.awaiting_shutdown_confirmation
            ):

                resposta = self._confirmation_response(
                    pergunta
                )

                yield {
                    "type":
                        "done",

                    "content":
                        resposta["response"],

                    "state":
                        resposta["state"],

                    "requires_confirmation":
                        resposta.get(
                            "requires_confirmation",
                            False
                        ),

                    "session_ended":
                        resposta.get(
                            "session_ended",
                            False
                        ),

                    "shutdown_requested":
                        resposta.get(
                            "shutdown_requested",
                            False
                        )
                }

                return


            # ========================================
            # VERIFICAÇÃO DE DESPEDIDA
            # ========================================

            self.state = "thinking"

            if deseja_encerrar(
                pergunta
            ):

                self.awaiting_confirmation = True

                self.state = "idle"

                yield {
                    "type":
                        "done",

                    "content":
                        "Deseja encerrar a sessão?",

                    "state":
                        "idle",

                    "requires_confirmation":
                        True,

                    "session_ended":
                        False,

                    "shutdown_requested":
                        False
                }

                return


            # ========================================
            # SELEÇÃO DE HISTÓRICO
            # ========================================

            if existe_selecao_pendente():

                resposta = selecionar_por_numero(
                    pergunta
                )

                if resposta:

                    self.state = "idle"

                    yield {
                        "type":
                            "done",

                        "content":
                            resposta,

                        "state":
                            "idle",

                        "requires_confirmation":
                            False,

                        "session_ended":
                            False,

                        "shutdown_requested":
                            False
                    }

                    return


            # ========================================
            # HISTÓRICO
            # ========================================

            acao_historico = analisar_historico(
                pergunta
            )

            if acao_historico in (
                "buscar",
                "abrir"
            ):

                resposta = buscar_historico(
                    pergunta
                )

                self.state = "idle"

                yield {
                    "type":
                        "done",

                    "content":
                        resposta,

                    "state":
                        "idle",

                    "requires_confirmation":
                        False,

                    "session_ended":
                        False,

                    "shutdown_requested":
                        False
                }

                return


            # ========================================
            # INICIAR SESSÃO NO HISTÓRICO
            # ========================================

            if not self.historico_iniciado:

                iniciar_historico(
                    pergunta
                )

                self.historico_iniciado = True


            adicionar_usuario(
                self.messages,
                pergunta
            )

            adicionar_mensagem(
                "user",
                pergunta
            )


            messages_para_envio = (
                self._preparar_mensagem(
                    pergunta
                )
            )

            self.state = "responding"

            partes = []


            for parte in enviar_mensagem_stream(
                messages_para_envio
            ):

                if not parte:
                    continue

                partes.append(
                    parte
                )

                yield {
                    "type":
                        "stream",

                    "content":
                        parte,

                    "state":
                        "responding"
                }


            resposta = "".join(
                partes
            )


            if not resposta:

                raise Exception(
                    "O modelo não retornou "
                    "uma resposta válida."
                )


            adicionar_assistente(
                self.messages,
                resposta
            )

            adicionar_mensagem(
                "assistant",
                resposta
            )

            self.state = "idle"


            yield {
                "type":
                    "done",

                "state":
                    "idle",

                "requires_confirmation":
                    False,

                "session_ended":
                    False,

                "shutdown_requested":
                    False
            }


        except Exception as erro:

            self.state = "error"

            log_error(
                str(erro)
            )

            yield {
                "type":
                    "error",

                "content":
                    mensagem_erro(erro),

                "state":
                    "error",

                "requires_confirmation":
                    False,

                "session_ended":
                    False,

                "shutdown_requested":
                    False
            }