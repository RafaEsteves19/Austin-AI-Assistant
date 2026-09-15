from core.engine.assistant import AustinAssistant


_assistant = None


def obter_assistente():
    global _assistant

    if _assistant is None:
        _assistant = AustinAssistant()

    return _assistant


def processar_mensagem(mensagem):
    return obter_assistente().process_message(
        mensagem
    )


def nova_sessao():
    return obter_assistente().new_session()


def status():
    return obter_assistente().status()
