def criar_conversa(instructions):

    if instructions is None:
        instructions = ""

    return [
        {
            "role": "system",
            "content": instructions
        }
    ]


def adicionar_usuario(messages, texto):

    messages.append(
        {
            "role": "user",
            "content": texto
        }
    )


def adicionar_assistente(messages, texto):

    messages.append(
        {
            "role": "assistant",
            "content": texto
        }
    )


def obter_historico(messages):

    return messages