import sys
from datetime import datetime
from pathlib import Path


# ==========================================================
# CAMINHO DA RAIZ DO PROJETO
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ==========================================================
# BANCO DE DADOS
# ==========================================================

from database.history.database import (
    obter_conexao,
    inicializar_banco
)


# ==========================================================
# ESTADO ATUAL
# ==========================================================

conversa_atual = None
conversa_selecionada = None


# ==========================================================
# PREPARAR HISTÓRICO
# ==========================================================

def preparar_history():
    """
    Garante que o banco de dados esteja inicializado.
    """

    inicializar_banco()


# ==========================================================
# CRIAR TÍTULO
# ==========================================================

def criar_titulo(texto):
    """
    Cria um título curto a partir da primeira mensagem.
    """

    palavras = str(texto).split()

    titulo = " ".join(
        palavras[:6]
    )

    return titulo or "Conversa"


# ==========================================================
# INICIAR HISTÓRICO
# ==========================================================

def iniciar_historico(primeira_mensagem):
    """
    Cria uma nova sessão no banco de dados.
    """

    global conversa_atual

    preparar_history()

    agora = datetime.now()

    titulo = criar_titulo(
        primeira_mensagem
    )

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO sessions (
                title,
                status
            )
            VALUES (?, ?)
            """,
            (
                titulo,
                "active"
            )
        )

        session_id = cursor.lastrowid

        conexao.commit()

        conversa_atual = {
            "id": session_id,
            "titulo": titulo,
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M:%S")
        }

        return session_id

    finally:
        conexao.close()


# ==========================================================
# ADICIONAR MENSAGEM
# ==========================================================

def adicionar_mensagem(role, content):
    """
    Adiciona uma mensagem à sessão atual.
    """

    if not conversa_atual:
        return

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (
                conversa_atual["id"],
                role,
                content
            )
        )

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# ATUALIZAR TÍTULO
# ==========================================================

def atualizar_titulo(session_id, titulo):
    """
    Atualiza o título de uma sessão.
    """

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE sessions
            SET title = ?
            WHERE id = ?
            """,
            (
                titulo,
                session_id
            )
        )

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# ATUALIZAR RESUMO
# ==========================================================

def atualizar_resumo(session_id, resumo):
    """
    Atualiza o resumo de uma sessão.
    """

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE sessions
            SET summary = ?
            WHERE id = ?
            """,
            (
                resumo,
                session_id
            )
        )

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# FINALIZAR HISTÓRICO
# ==========================================================

def finalizar_historico():
    """
    Finaliza a sessão atual.
    """

    if not conversa_atual:
        return

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE sessions
            SET
                status = ?,
                ended_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                "ended",
                conversa_atual["id"]
            )
        )

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# BUSCAR CONVERSAS
# ==========================================================

def buscar_conversas():
    """
    Retorna as conversas disponíveis,
    da mais recente para a mais antiga.
    """

    preparar_history()

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                summary,
                created_at,
                ended_at,
                status
            FROM sessions
            ORDER BY created_at DESC
            """
        )

        resultados = cursor.fetchall()

        conversas = []

        for conversa in resultados:
            data_hora = conversa["created_at"]

            data = ""
            hora = ""

            if data_hora:
                partes = data_hora.split(" ")

                if len(partes) >= 2:
                    data = partes[0]
                    hora = partes[1]

            conversas.append({
                "id": conversa["id"],
                "titulo": conversa["title"] or "Conversa",
                "summary": conversa["summary"],
                "data": data,
                "hora": hora,
                "status": conversa["status"],
                "created_at": conversa["created_at"],
                "ended_at": conversa["ended_at"]
            })

        return conversas

    finally:
        conexao.close()


# ==========================================================
# BUSCAR CONVERSAS POR TEXTO
# ==========================================================

def buscar_conversas_por_texto(texto):
    """
    Busca conversas pelo título ou resumo.

    Essa é a primeira camada da busca semântica.
    """

    preparar_history()

    texto = str(texto).strip()

    if not texto:
        return []

    termo = f"%{texto}%"

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                summary,
                created_at,
                ended_at,
                status
            FROM sessions
            WHERE
                title LIKE ?
                OR summary LIKE ?
            ORDER BY created_at DESC
            """,
            (
                termo,
                termo
            )
        )

        resultados = cursor.fetchall()

        conversas = []

        for conversa in resultados:
            data_hora = conversa["created_at"]

            data = ""
            hora = ""

            if data_hora:
                partes = data_hora.split(" ")

                if len(partes) >= 2:
                    data = partes[0]
                    hora = partes[1]

            conversas.append({
                "id": conversa["id"],
                "titulo": conversa["title"] or "Conversa",
                "summary": conversa["summary"],
                "data": data,
                "hora": hora,
                "status": conversa["status"],
                "created_at": conversa["created_at"],
                "ended_at": conversa["ended_at"]
            })

        return conversas

    finally:
        conexao.close()


# ==========================================================
# SELECIONAR CONVERSA
# ==========================================================

def selecionar_conversa(session_id):
    """
    Seleciona uma conversa pelo ID.
    """

    global conversa_selecionada

    conversa_selecionada = session_id


# ==========================================================
# CARREGAR CONVERSA
# ==========================================================

def carregar_conversa(session_id):
    """
    Carrega uma conversa completa, incluindo suas mensagens.
    """

    if not session_id:
        return None

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                summary,
                created_at,
                ended_at,
                status
            FROM sessions
            WHERE id = ?
            """,
            (session_id,)
        )

        sessao = cursor.fetchone()

        if not sessao:
            return None

        cursor.execute(
            """
            SELECT
                id,
                role,
                content,
                created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,)
        )

        mensagens = cursor.fetchall()

        return {
            "id": sessao["id"],
            "titulo": sessao["title"] or "Conversa",
            "summary": sessao["summary"],
            "data": (
                sessao["created_at"].split(" ")[0]
                if sessao["created_at"]
                else ""
            ),
            "hora": (
                sessao["created_at"].split(" ")[1]
                if sessao["created_at"] and " " in sessao["created_at"]
                else ""
            ),
            "status": sessao["status"],
            "created_at": sessao["created_at"],
            "ended_at": sessao["ended_at"],
            "mensagens": [
                {
                    "id": mensagem["id"],
                    "role": mensagem["role"],
                    "content": mensagem["content"],
                    "created_at": mensagem["created_at"]
                }
                for mensagem in mensagens
            ]
        }

    finally:
        conexao.close()


# ==========================================================
# CARREGAR CONVERSA SELECIONADA
# ==========================================================

def carregar_conversa_selecionada():
    """
    Carrega a conversa atualmente selecionada.
    """

    if not conversa_selecionada:
        return None

    return carregar_conversa(
        conversa_selecionada
    )


# ==========================================================
# ENCONTRAR CONVERSA
# ==========================================================

def encontrar_conversa(texto):
    """
    Procura uma conversa pelo título ou resumo.

    Retorna:
        - uma conversa, quando há apenas uma correspondência;
        - None, quando não encontra;
        - lista de conversas, quando há múltiplas correspondências.
    """

    resultados = buscar_conversas_por_texto(
        texto
    )

    if len(resultados) == 1:
        return resultados[0]

    if len(resultados) > 1:
        return resultados

    return None


# ==========================================================
# OBTER CONVERSA ATUAL
# ==========================================================

def obter_conversa_atual():
    """
    Retorna os dados da sessão atual.
    """

    return conversa_atual


# ==========================================================
# OBTER CONVERSA SELECIONADA
# ==========================================================

def obter_conversa_selecionada():
    """
    Retorna o ID da conversa selecionada.
    """

    return conversa_selecionada


# ==========================================================
# TESTE DIRETO
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TESTE DO HISTORY MANAGER")
    print("=" * 60)

    preparar_history()

    print()
    print("Banco de dados inicializado com sucesso.")

    conversas = buscar_conversas()

    print()
    print(f"Conversas encontradas: {len(conversas)}")

    for conversa in conversas:
        print(
            f"[{conversa['id']}] "
            f"{conversa['titulo']} "
            f"({conversa['data']} {conversa['hora']})"
        )

    print()
    print("History Manager funcionando.")