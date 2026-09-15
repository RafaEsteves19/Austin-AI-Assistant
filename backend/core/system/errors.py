def mensagem_erro(erro):

    erro_texto = str(erro).lower()


    if "401" in erro_texto or "unauthorized" in erro_texto:

        return (
            "Peço desculpas, Sr. Esteves. "
            "As credenciais de acesso parecem inválidas."
        )


    if "429" in erro_texto or "rate limit" in erro_texto:

        return (
            "Peço desculpas, Sr. Esteves. "
            "O limite de requisições foi atingido."
        )


    if "connection" in erro_texto or "timeout" in erro_texto:

        return (
            "Peço desculpas, Sr. Esteves. "
            "Não consegui estabelecer comunicação com o serviço."
        )


    return (
        "Peço desculpas, Sr. Esteves. "
        "Detectei uma falha inesperada nos sistemas."
    )