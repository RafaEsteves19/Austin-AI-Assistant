import sys
import json
import re
import unicodedata
from pathlib import Path


# ==========================================================
# CONFIGURAÇÃO DOS CAMINHOS DO PROJETO
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from history.history_manager import (
    buscar_conversas,
    buscar_conversas_por_texto,
    selecionar_conversa,
    carregar_conversa_selecionada
)

from history.history_context import (
    adicionar_contexto_historico
)

from core.ai.model_manager import (
    enviar_mensagem
)


# ==========================================================
# ESTADO DA BUSCA
# ==========================================================

conversas_exibidas = []
aguardando_selecao = False


# ==========================================================
# VERIFICAR SE EXISTE SELEÇÃO PENDENTE
# ==========================================================

def existe_selecao_pendente():
    return aguardando_selecao


# ==========================================================
# NORMALIZAR TEXTO
# ==========================================================

def _normalizar(texto):
    """
    Normaliza um texto para facilitar comparações.

    Remove:
    - maiúsculas/minúsculas;
    - acentos;
    - pontuação;
    - espaços.

    Exemplo:

    "Desenvolvimento de IA com Python"

    vira:

    "desenvolvimentodeiacompython"
    """

    texto = str(
        texto
    ).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = re.sub(
        r"[^a-z0-9]+",
        "",
        texto
    )

    return texto


# ==========================================================
# EXTRAIR PALAVRAS IMPORTANTES
# ==========================================================

def _extrair_palavras_importantes(texto):
    """
    Extrai palavras relevantes para comparação.

    Palavras muito curtas são ignoradas.
    """

    palavras = [
        _normalizar(
            palavra
        )
        for palavra in str(texto).split()
    ]

    return [
        palavra
        for palavra in palavras
        if len(palavra) >= 4
    ]


# ==========================================================
# ABRIR CONVERSA
# ==========================================================

def _abrir_conversa(conversa):
    """
    Seleciona uma conversa pelo ID e carrega
    seu conteúdo completo somente neste momento.
    """

    global aguardando_selecao

    session_id = conversa.get(
        "id"
    )

    if not session_id:
        return (
            "Não foi possível identificar "
            "essa conversa."
        )

    selecionar_conversa(
        session_id
    )

    aguardando_selecao = False

    resumo = resumir_conversa()

    adicionar_contexto_historico(
        resumo
    )

    return resumo


# ==========================================================
# ENCONTRAR CONVERSA POR TEXTO
# ==========================================================

def _encontrar_por_texto(
    pergunta,
    conversas
):
    """
    Tenta encontrar a conversa mais relacionada
    ao pedido do usuário.

    A busca acontece em camadas:

    1. correspondência exata com o título;
    2. correspondência exata com o resumo;
    3. palavras do pedido no título;
    4. palavras do pedido no resumo;
    5. pontuação combinada.

    Retorna:

    - conversa quando há uma correspondência clara;
    - lista quando existem múltiplas possibilidades;
    - None quando não encontra.
    """

    pergunta_normalizada = _normalizar(
        pergunta
    )

    if not pergunta_normalizada:
        return None

    # ======================================================
    # 1. TÍTULO COMPLETO DENTRO DO PEDIDO
    # ======================================================

    correspondencias_titulo = []

    for conversa in conversas:

        titulo = _normalizar(
            conversa.get(
                "titulo",
                ""
            )
        )

        if (
            titulo
            and titulo in pergunta_normalizada
        ):
            correspondencias_titulo.append(
                conversa
            )

    if len(correspondencias_titulo) == 1:
        return correspondencias_titulo[0]

    if len(correspondencias_titulo) > 1:
        return correspondencias_titulo

    # ======================================================
    # 2. RESUMO COMPLETO DENTRO DO PEDIDO
    # ======================================================

    correspondencias_resumo = []

    for conversa in conversas:

        resumo = _normalizar(
            conversa.get(
                "summary",
                ""
            ) or ""
        )

        if (
            resumo
            and len(resumo) >= 10
            and resumo in pergunta_normalizada
        ):
            correspondencias_resumo.append(
                conversa
            )

    if len(correspondencias_resumo) == 1:
        return correspondencias_resumo[0]

    if len(correspondencias_resumo) > 1:
        return correspondencias_resumo

    # ======================================================
    # 3. PALAVRAS IMPORTANTES
    # ======================================================

    palavras = _extrair_palavras_importantes(
        pergunta
    )

    if not palavras:
        return None

    pontuacoes = []

    for conversa in conversas:

        titulo = _normalizar(
            conversa.get(
                "titulo",
                ""
            )
        )

        resumo = _normalizar(
            conversa.get(
                "summary",
                ""
            ) or ""
        )

        pontuacao_titulo = 0
        pontuacao_resumo = 0

        for palavra in palavras:

            if palavra in titulo:
                pontuacao_titulo += 3

            if palavra in resumo:
                pontuacao_resumo += 1

        pontuacao_total = (
            pontuacao_titulo
            +
            pontuacao_resumo
        )

        if pontuacao_total > 0:

            pontuacoes.append(
                (
                    pontuacao_total,
                    conversa
                )
            )

    if not pontuacoes:
        return None

    # Ordena da maior pontuação para a menor.
    pontuacoes.sort(
        key=lambda item: item[0],
        reverse=True
    )

    maior_pontuacao = pontuacoes[0][0]

    melhores = [
        conversa
        for pontuacao, conversa
        in pontuacoes
        if pontuacao == maior_pontuacao
    ]

    # ======================================================
    # CORRESPONDÊNCIA CLARA
    # ======================================================

    if (
        maior_pontuacao >= 3
        and len(melhores) == 1
    ):
        return melhores[0]

    # ======================================================
    # MÚLTIPLAS POSSIBILIDADES
    # ======================================================

    if len(melhores) > 1:
        return melhores

    return None


# ==========================================================
# BUSCA SEMÂNTICA COM O MODELO
# ==========================================================

def _interpretar_busca_com_modelo(
    pergunta,
    conversas
):
    """
    Usa o modelo somente quando a busca local
    não consegue determinar claramente a conversa.

    Retorna:

    - NUMERO:X
    - LISTAR
    """

    if not conversas:
        return "LISTAR"

    contexto = json.dumps(
        [
            {
                "numero": indice,
                "id": conversa.get(
                    "id"
                ),
                "titulo": conversa.get(
                    "titulo",
                    ""
                ),
                "resumo": conversa.get(
                    "summary",
                    ""
                ),
                "data": conversa.get(
                    "data",
                    ""
                )
            }
            for indice, conversa
            in enumerate(
                conversas,
                start=1
            )
        ],
        indent=4,
        ensure_ascii=False
    )

    resposta = enviar_mensagem(
        [
            {
                "role": "system",
                "content": """
Você é um sistema de busca de histórico.

Analise o pedido do usuário e as conversas disponíveis.

Escolha uma conversa SOMENTE quando houver
uma relação clara entre o pedido e o título ou resumo.

Se houver uma correspondência clara,
responda somente:

NUMERO:X

onde X é o número exibido.

Se não houver correspondência clara,
responda somente:

LISTAR

Nunca invente números.
Nunca explique sua resposta.
Nunca retorne texto adicional.
"""
            },
            {
                "role": "user",
                "content": f"""
Pedido do usuário:

{pergunta}

Conversas disponíveis:

{contexto}
"""
            }
        ],
        temperature=0,
        max_tokens=5
    )

    if not resposta:
        return "LISTAR"

    return (
        resposta
        .strip()
        .upper()
    )


# ==========================================================
# BUSCAR HISTÓRICO
# ==========================================================

def buscar_historico(pergunta):
    """
    Principal função de busca do histórico.

    Permite:

    - listar histórico;
    - selecionar por número;
    - encontrar por título;
    - encontrar por assunto;
    - encontrar por resumo;
    - utilizar o modelo para casos ambíguos.
    """

    global conversas_exibidas
    global aguardando_selecao

    conversas = buscar_conversas()

    if not conversas:
        aguardando_selecao = False

        return (
            "Não encontrei conversas salvas "
            "no histórico."
        )

    # ======================================================
    # BUSCA DIRETA LOCAL
    # ======================================================

    resultado_direto = _encontrar_por_texto(
        pergunta,
        conversas
    )

    # Uma conversa claramente encontrada.
    if isinstance(
        resultado_direto,
        dict
    ):

        aguardando_selecao = False

        return _abrir_conversa(
            resultado_direto
        )

    # Mais de uma conversa semelhante.
    if isinstance(
        resultado_direto,
        list
    ) and resultado_direto:

        conversas_exibidas = (
            resultado_direto[:10]
        )

        aguardando_selecao = True

        return listar_conversas(
            mensagem=(
                "Encontrei algumas conversas "
                "que podem ser relacionadas "
                "ao que você pediu:"
            )
        )

    # ======================================================
    # BUSCA PELO MODELO
    # ======================================================

    conversas_exibidas = conversas[:10]

    resultado = _interpretar_busca_com_modelo(
        pergunta,
        conversas_exibidas
    )

    # ======================================================
    # MODELO ESCOLHEU UMA CONVERSA
    # ======================================================

    if resultado.startswith(
        "NUMERO:"
    ):

        try:

            numero = int(
                resultado
                .replace(
                    "NUMERO:",
                    ""
                )
                .strip()
            )

            if (
                1
                <= numero
                <= len(conversas_exibidas)
            ):

                aguardando_selecao = False

                return abrir_por_numero(
                    numero
                )

        except (
            ValueError,
            TypeError
        ):
            pass

    # ======================================================
    # NÃO FOI POSSÍVEL IDENTIFICAR
    # ======================================================

    aguardando_selecao = True

    return listar_conversas()


# ==========================================================
# LISTAR CONVERSAS
# ==========================================================

def listar_conversas(
    mensagem=None
):
    """
    Exibe as conversas disponíveis
    para seleção manual.
    """

    if mensagem is None:

        mensagem = (
            "Encontrei estas conversas:"
        )

    resposta = (
        f"{mensagem}\n\n"
    )

    for indice, conversa in enumerate(
        conversas_exibidas,
        start=1
    ):

        titulo = conversa.get(
            "titulo",
            "Conversa"
        )

        data = conversa.get(
            "data",
            ""
        )

        resposta += (
            f"{indice}. "
            f"{titulo}"
        )

        if data:
            resposta += (
                f" ({data})"
            )

        resposta += "\n"

    resposta += (
        "\nDigite o número da conversa "
        "que deseja abrir."
    )

    return resposta


# ==========================================================
# SELECIONAR POR NÚMERO
# ==========================================================

def selecionar_por_numero(texto):
    """
    Abre uma conversa a partir do número
    mostrado na listagem.
    """

    global aguardando_selecao

    if not aguardando_selecao:
        return None

    texto = str(
        texto
    ).strip()

    if not texto.isdigit():

        aguardando_selecao = False

        return None

    numero = int(
        texto
    )

    resposta = abrir_por_numero(
        numero
    )

    aguardando_selecao = False

    return resposta


# ==========================================================
# ABRIR POR NÚMERO
# ==========================================================

def abrir_por_numero(numero):
    """
    Abre uma conversa utilizando o número
    apresentado ao usuário.
    """

    if numero < 1:
        return "Número inválido."

    indice = numero - 1

    if indice >= len(
        conversas_exibidas
    ):

        return (
            "Essa conversa não existe."
        )

    conversa = conversas_exibidas[
        indice
    ]

    return _abrir_conversa(
        conversa
    )


# ==========================================================
# ABRIR HISTÓRICO
# ==========================================================

def abrir_historico(pergunta):
    """
    Alias utilizado pelo restante do sistema.
    """

    return buscar_historico(
        pergunta
    )


# ==========================================================
# RESUMIR CONVERSA
# ==========================================================

def resumir_conversa():
    """
    Carrega a conversa selecionada e gera
    um resumo detalhado para servir como
    contexto da conversa atual.
    """

    conversa = (
        carregar_conversa_selecionada()
    )

    if not conversa:

        return (
            "Não encontrei a conversa "
            "selecionada."
        )

    contexto = json.dumps(
        conversa,
        indent=4,
        ensure_ascii=False
    )

    resposta = enviar_mensagem(
        [
            {
                "role": "system",
                "content": """
Analise a conversa antiga.

Crie um resumo detalhado para ser usado
como contexto de continuação da conversa atual.

Inclua:

- assunto principal;
- informações importantes;
- decisões tomadas;
- detalhes técnicos;
- nomes;
- arquivos;
- números;
- valores;
- configurações;
- problemas encontrados;
- soluções adotadas;
- contexto necessário para continuar.

Não faça uma análise genérica.

Preserve detalhes concretos que possam ser
necessários nas próximas perguntas do usuário.

Retorne somente o resumo.
"""
            },
            {
                "role": "user",
                "content": contexto
            }
        ]
    )

    return resposta