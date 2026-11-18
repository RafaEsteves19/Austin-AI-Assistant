
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MEMORY_DIR = (
    PROJECT_ROOT
    / "database"
    / "user"
    / "memory"
)

MEMORY_CATEGORIES = {
    "development": "development.md",
    "projects": "projects.md",
    "workflow": "workflow.md",
    "general": "general.md",
}


def preparar_memoria():
    """Garante que os arquivos de memória existam."""

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    for filename in MEMORY_CATEGORIES.values():
        file_path = MEMORY_DIR / filename

        if not file_path.exists():
            file_path.write_text(
                "# Memórias\n",
                encoding="utf-8"
            )


def _obter_arquivo(categoria):
    if categoria not in MEMORY_CATEGORIES:
        raise ValueError(
            f"Categoria de memória inválida: {categoria}"
        )

    return MEMORY_DIR / MEMORY_CATEGORIES[categoria]


def _ler_entradas(categoria):
    preparar_memoria()

    file_path = _obter_arquivo(categoria)
    content = file_path.read_text(encoding="utf-8")

    entries = []
    current = None

    for line in content.splitlines():
        if line.startswith("## ID: "):
            if current:
                entries.append(current)

            current = {
                "id": line.replace("## ID: ", "", 1).strip(),
                "date": "",
                "content": "",
            }

        elif current and line.startswith("- Data: "):
            current["date"] = line.replace(
                "- Data: ", "", 1
            ).strip()

        elif current and line.startswith("- Conteúdo: "):
            current["content"] = line.replace(
                "- Conteúdo: ", "", 1
            ).strip()

    if current:
        entries.append(current)

    return entries


def salvar_memoria(categoria, conteudo):
    """Armazena uma nova memória."""

    conteudo = conteudo.strip()

    if not conteudo:
        raise ValueError("A memória não pode estar vazia.")

    preparar_memoria()

    memory_id = str(uuid4())
    date = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    file_path = _obter_arquivo(categoria)

    entry = (
        f"\n## ID: {memory_id}\n"
        f"- Data: {date}\n"
        f"- Conteúdo: {conteudo}\n"
    )

    with file_path.open("a", encoding="utf-8") as file:
        file.write(entry)

    return {
        "id": memory_id,
        "category": categoria,
        "date": date,
        "content": conteudo,
    }


def listar_memorias(categoria=None):
    """Lista as memórias armazenadas."""

    preparar_memoria()

    if categoria is not None:
        return _ler_entradas(categoria)

    memories = []

    for category in MEMORY_CATEGORIES:
        for entry in _ler_entradas(category):
            memories.append({
                **entry,
                "category": category,
            })

    return memories


def buscar_memorias(termo, categoria=None):
    """Busca memórias pelo conteúdo."""

    termo = termo.strip().casefold()

    if not termo:
        return []

    memories = listar_memorias(categoria)

    return [
        memory
        for memory in memories
        if termo in memory["content"].casefold()
    ]


def atualizar_memoria(memory_id, novo_conteudo):
    """Atualiza uma memória existente."""

    novo_conteudo = novo_conteudo.strip()

    if not novo_conteudo:
        raise ValueError("A memória não pode estar vazia.")

    for categoria in MEMORY_CATEGORIES:
        entries = _ler_entradas(categoria)

        for entry in entries:
            if entry["id"] == memory_id:
                entry["content"] = novo_conteudo
                entry["date"] = datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )

                _reescrever_arquivo(categoria, entries)
                return True

    return False


def remover_memoria(memory_id):
    """Remove uma memória pelo identificador."""

    for categoria in MEMORY_CATEGORIES:
        entries = _ler_entradas(categoria)

        filtered = [
            entry
            for entry in entries
            if entry["id"] != memory_id
        ]

        if len(filtered) != len(entries):
            _reescrever_arquivo(categoria, filtered)
            return True

    return False


def _reescrever_arquivo(categoria, entries):
    file_path = _obter_arquivo(categoria)

    content = "# Memórias\n"

    for entry in entries:
        content += (
            f"\n## ID: {entry['id']}\n"
            f"- Data: {entry['date']}\n"
            f"- Conteúdo: {entry['content']}\n"
        )

    file_path.write_text(content, encoding="utf-8")
