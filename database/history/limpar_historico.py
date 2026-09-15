import sys
from pathlib import Path


# ==========================================================
# CAMINHO DA PASTA DO BANCO
# ==========================================================
DATABASE_DIR = Path(__file__).resolve().parent

if str(DATABASE_DIR) not in sys.path:
    sys.path.insert(0, str(DATABASE_DIR))


from database import zerar_historico


def main():
    print("=" * 60)
    print("LIMPEZA DO HISTÓRICO AUSTIN")
    print("=" * 60)
    print()

    confirmacao = input(
        "Tem certeza que deseja apagar TODO o histórico? (s/n): "
    ).strip().lower()

    if confirmacao not in ("s", "sim"):
        print()
        print("Operação cancelada.")
        return

    zerar_historico()

    print()
    print("Histórico apagado com sucesso.")
    print("Os IDs das sessões foram reiniciados.")
    print()


if __name__ == "__main__":
    main()