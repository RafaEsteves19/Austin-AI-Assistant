import sqlite3
from pathlib import Path


# ==========================================================
# CAMINHO DO BANCO DE DADOS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "austin.db"


# ==========================================================
# CONEXÃO
# ==========================================================

def obter_conexao():
    """
    Retorna uma conexão com o banco de dados SQLite.
    """

    conexao = sqlite3.connect(DB_PATH)

    # Permite acessar colunas pelo nome
    conexao.row_factory = sqlite3.Row

    # Ativa suporte às chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# ==========================================================
# INICIALIZAÇÃO
# ==========================================================

def inicializar_banco():
    """
    Cria as tabelas necessárias do banco de dados.
    """

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        # ==================================================
        # SESSÕES
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ended_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                title TEXT,
                summary TEXT
            )
        """)

        # ==================================================
        # MENSAGENS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id)
                    ON DELETE CASCADE
            )
        """)

        # ==================================================
        # ÍNDICES
        # ==================================================

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at
            ON sessions(created_at)
        """)

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# LIMPAR HISTÓRICO
# ==========================================================

def zerar_historico():
    """
    Apaga todo o histórico do banco de dados
    e reinicia a numeração dos IDs das sessões.

    Esta função é destinada ao uso manual pelo terminal.

    Não é chamada automaticamente pelo History Manager.
    """

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()

        # Apaga primeiro as mensagens
        cursor.execute("DELETE FROM messages")

        # Depois apaga as sessões
        cursor.execute("DELETE FROM sessions")

        # Reinicia o contador AUTOINCREMENT da tabela sessions
        cursor.execute("""
            DELETE FROM sqlite_sequence
            WHERE name = 'sessions'
        """)

        conexao.commit()

    finally:
        conexao.close()


# ==========================================================
# TESTE DIRETO
# ==========================================================

if __name__ == "__main__":
    inicializar_banco()

    print("=" * 60)
    print("BANCO DE DADOS AUSTIN - HISTÓRICO")
    print("=" * 60)
    print()
    print("Banco inicializado em:")
    print(DB_PATH)
    print()