import random


saudacoes = [
    "Olá, Sr. Esteves. Sistemas online e aguardando suas instruções.",
    "Bom dia, Sr. Esteves. Todos os sistemas estão operacionais.",
    "Olá, Sr. Esteves. É um prazer iniciar uma nova sessão.",
    "Bem-vindo novamente, Sr. Esteves. Estou pronto para auxiliar.",
    "Olá, Sr. Esteves. Minha interface foi carregada e estou à disposição."
]


def saudacao_inicial():

    return random.choice(saudacoes)