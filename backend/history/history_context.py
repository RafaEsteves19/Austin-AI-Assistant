contexto_historico = None


def adicionar_contexto_historico(resumo):
    global contexto_historico
    contexto_historico = resumo


def obter_contexto_historico():
    return contexto_historico


def limpar_contexto_historico():
    global contexto_historico
    contexto_historico = None
