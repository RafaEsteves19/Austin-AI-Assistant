def ler_arquivo(caminho):

    try:

        with open(
            caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return arquivo.read()


    except FileNotFoundError:

        return None



def escrever_arquivo(caminho, conteudo):

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(conteudo)