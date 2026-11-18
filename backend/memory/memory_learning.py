
import json
import re
import unicodedata
from difflib import SequenceMatcher

from core.ai.model_manager import enviar_mensagem

from memory.memory_manager import (
    salvar_memoria,
    listar_memorias,
)


CATEGORIES = {
    "development",
    "projects",
    "workflow",
    "general",
}


# Expressões que indicam uma solicitação explícita.
# Os textos são comparados sem acentos.
EXPLICIT_PATTERNS = [
    r"lembre-se de que",
    r"lembre-se que",
    r"lembre de que",
    r"lembre que",
    r"guarde que",
    r"memorize que",
    r"anote que",
    r"registre que",
    r"quero que voce lembre",
    r"quero que voce se lembre",
    r"quero que voce guarde",
    r"guarde isso",
    r"anote isso",
    r"memorize isso",
]


BLOCKED_PHRASES = (
    "nao guarde",
    "nao memorize",
    "nao lembre",
    "nao armazene",
    "nao salve",
    "nao quero que voce guarde",
    "nao quero que voce memorize",
    "nao quero que voce lembre",
)


STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "sobre",
    "que", "se", "e", "ou", "mas", "como", "quando",
    "onde", "porque", "qual", "quais", "quem", "eu",
    "me", "meu", "minha", "meus", "minhas", "voce",
    "ele", "ela", "eles", "elas", "isso", "essa",
    "esse", "esta", "este", "aquela", "aquele",
    "sou", "estou", "tenho", "quero", "gosto",
    "prefiro", "muito", "mais", "menos", "tambem",
    "ser", "ter", "estar", "fazer", "usar",
    "foi", "era", "sao", "foi", "vai", "vou",
    "pode", "podemos", "deve", "deveria",
}


def _normalize(text):
    """Remove acentos e normaliza o texto para comparações."""

    text = str(text or "").strip().lower()

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def _limpar_conteudo(text):
    """Prepara o conteúdo para armazenamento em uma única linha."""

    text = str(text or "")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip(" \t\r\n.,;:-")


def permite_aprendizado_automatico(text):
    """Verifica se o usuário proibiu o armazenamento da mensagem."""

    normalized = _normalize(text)

    return not any(
        phrase in normalized
        for phrase in BLOCKED_PHRASES
    )


def _contem_informacao_sensivel(text):
    """
    Impede o armazenamento de credenciais e dados
    que não devem entrar na memória do assistente.
    """

    normalized = _normalize(text)

    sensitive_patterns = [
        r"\bsenha\b",
        r"\bpassword\b",
        r"\bpassphrase\b",
        r"\bapi[\s_-]?key\b",
        r"\bchave[\s_-]?de[\s_-]?api\b",
        r"\baccess[\s_-]?token\b",
        r"\brefresh[\s_-]?token\b",
        r"\btoken[\s_-]?de[\s_-]?acesso\b",
        r"\bsecret[\s_-]?key\b",
        r"\bclient[\s_-]?secret\b",
        r"\bprivate[\s_-]?key\b",
        r"\bchave[\s_-]?privada\b",
        r"\bbearer\s+[a-z0-9._-]{12,}\b",
        r"\bsk-[a-z0-9_-]{12,}\b",
        r"\bgh[pousr]_[a-z0-9]{20,}\b",
        r"\b-----begin [a-z ]*private key-----",
        r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    ]

    return any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in sensitive_patterns
    )


def _identificar_categoria(text):
    """Escolhe uma categoria inicial por palavras-chave."""

    normalized = _normalize(text)

    development_terms = (
        "python", "javascript", "typescript", "react",
        "programacao", "programador", "codigo", "software",
        "desenvolvimento", "linguagem", "framework",
        "biblioteca", "api", "backend", "frontend",
        "ma ui", "dotnet", "csharp", "java", "html",
        "css", "sql", "terminal", "linux",
    )

    project_terms = (
        "projeto", "aplicativo", "aplicacao", "sistema",
        "site", "website", "repositorio", "austin",
        "desenvolvendo", "construindo", "produto",
    )

    workflow_terms = (
        "prefiro", "gosto de", "quero que",
        "sempre", "nunca", "formato", "resposta",
        "completo", "passo a passo", "workflow",
        "metodo", "metodologia", "organizar",
    )

    if any(term in normalized for term in project_terms):
        return "projects"

    if any(term in normalized for term in workflow_terms):
        return "workflow"

    if any(term in normalized for term in development_terms):
        return "development"

    return "general"


def _conteudo_ja_existe(conteudo):
    """Evita memórias iguais ou praticamente idênticas."""

    normalized_new = _normalize(conteudo)

    for memory in listar_memorias():
        existing = _normalize(
            memory.get("content", "")
        )

        if not existing:
            continue

        if normalized_new == existing:
            return True

        similarity = SequenceMatcher(
            None,
            normalized_new,
            existing
        ).ratio()

        if similarity >= 0.96:
            return True

    return False


def guardar_memoria_explicita(user_message):
    """
    Identifica pedidos explícitos e armazena a informação
    imediatamente, sem chamar o modelo para classificá-la.
    """

    if not user_message:
        return None

    normalized = _normalize(user_message)

    # Uma proibição explícita nunca deve virar uma memorização.
    if not permite_aprendizado_automatico(user_message):
        return None

    match = None

    for pattern in EXPLICIT_PATTERNS:
        match = re.search(
            pattern,
            normalized
        )

        if match:
            break

    if not match:
        return None

    # A normalização preserva os índices dos caracteres
    # para extrair o conteúdo da mensagem original.
    conteudo = _limpar_conteudo(
        user_message[match.end():]
    )

    if not conteudo:
        return None

    if _contem_informacao_sensivel(conteudo):
        return {
            "status": "blocked",
            "content": conteudo,
        }

    if _conteudo_ja_existe(conteudo):
        return {
            "status": "already_exists",
            "content": conteudo,
        }

    categoria = _identificar_categoria(
        conteudo
    )

    memoria = salvar_memoria(
        categoria,
        conteudo
    )

    return {
        "status": "saved",
        "memory": memoria,
    }


def _extrair_json(response):
    """Extrai um objeto JSON mesmo se o modelo usar bloco Markdown."""

    if isinstance(response, dict):
        return response

    text = str(response or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except (json.JSONDecodeError, TypeError):
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end <= start:
        return None

    try:
        result = json.loads(
            text[start:end + 1]
        )

        if isinstance(result, dict):
            return result

    except (json.JSONDecodeError, TypeError):
        return None

    return None


def analisar_memoria_automatica(
    user_message,
    assistant_response
):
    """
    Analisa a interação depois da resposta principal.

    O modelo decide se existe uma informação persistente
    que vale a pena guardar. Erros nesta etapa não devem
    interromper o funcionamento normal do Austin.
    """

    try:

        if not user_message or not assistant_response:
            return None

        if not permite_aprendizado_automatico(
            user_message
        ):
            return None

        interaction = (
            f"Mensagem do usuário:\n{user_message}\n\n"
            f"Resposta do Austin:\n{assistant_response}"
        )

        # Evita enviar informações sensíveis ao classificador
        # e impede que sejam armazenadas automaticamente.
        if _contem_informacao_sensivel(interaction):
            return None

        prompt = """
Você é o módulo de memória de longo prazo do assistente Austin.

Analise a interação fornecida e decida se existe uma informação
útil, estável e relevante sobre o usuário que deva ser lembrada
em conversas futuras.

Armazene somente informações como:
- Preferências persistentes.
- Tecnologias que o usuário utiliza ou está aprendendo.
- Projetos em andamento e suas características.
- Preferências de desenvolvimento e organização.
- Informações gerais estáveis que ajudem em conversas futuras.

NÃO armazene:
- Perguntas comuns ou dúvidas pontuais.
- Respostas factuais sem relação com o usuário.
- Informações temporárias ou triviais.
- Suposições sobre o usuário.
- Senhas, tokens, chaves, credenciais ou dados financeiros.
- Dados pessoais sensíveis.
- Informações que não estejam claramente sustentadas pela interação.

Não transforme uma intenção passageira em uma preferência permanente.
Por exemplo, "estou aprendendo Java" pode ser uma informação útil,
mas uma pergunta sobre Java não significa que o usuário esteja
estudando essa linguagem.

Escolha apenas uma categoria:
development, projects, workflow ou general.

Responda exclusivamente com JSON válido neste formato:

{
    "save": true,
    "category": "development",
    "memory": "O usuário está aprendendo Java.",
    "confidence": 0.95
}

Se não houver informação que mereça ser guardada, responda:

{
    "save": false,
    "category": "general",
    "memory": "",
    "confidence": 0.0
}

A confiança deve variar de 0.0 a 1.0.
Só recomende salvar informações com confiança igual ou superior a 0.85.
"""

        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": interaction,
            },
        ]

        response = enviar_mensagem(
            messages,
            temperature=0.1,
            max_tokens=300
        )

        result = _extrair_json(
            response
        )

        if not result:
            return None

        if result.get("save") is not True:
            return None

        category = str(
            result.get("category", "general")
        ).strip().lower()

        if category not in CATEGORIES:
            return None

        content = _limpar_conteudo(
            result.get("memory", "")
        )

        if not content:
            return None

        try:
            confidence = float(
                result.get("confidence", 0)
            )
        except (TypeError, ValueError):
            return None

        if confidence < 0.85 or confidence > 1:
            return None

        if _contem_informacao_sensivel(content):
            return None

        if _conteudo_ja_existe(content):
            return {
                "status": "already_exists",
                "content": content,
            }

        memory = salvar_memoria(
            category,
            content
        )

        return {
            "status": "saved",
            "memory": memory,
        }

    except Exception as erro:
        # O aprendizado é complementar.
        # Uma falha nele não pode derrubar a conversa.
        try:
            from core.system.logs import log_error

            log_error(
                f"Erro no aprendizado automático: {erro}"
            )
        except Exception:
            pass

        return None


def obter_memorias_relevantes(
    user_message,
    limite=5
):
    """
    Recupera memórias relacionadas à mensagem atual
    usando correspondência simples de palavras.
    """

    if not user_message:
        return []

    normalized = _normalize(
        user_message
    )

    words = {
        word
        for word in re.findall(
            r"[a-z0-9+#.]+",
            normalized
        )
        if len(word) > 2 and word not in STOPWORDS
    }

    if not words:
        return []

    memories = listar_memorias()

    relevant = []

    for memory in memories:

        content = memory.get(
            "content",
            ""
        )

        normalized_content = _normalize(
            content
        )

        memory_words = {
            word
            for word in re.findall(
                r"[a-z0-9+#.]+",
                normalized_content
            )
            if len(word) > 2 and word not in STOPWORDS
        }

        overlap = words.intersection(
            memory_words
        )

        if not overlap:
            continue

        relevant.append({
            **memory,
            "_relevance": len(overlap),
        })

    relevant.sort(
        key=lambda item: item["_relevance"],
        reverse=True
    )

    results = []

    for memory in relevant[:limite]:
        memory.pop("_relevance", None)
        results.append(memory)

    return results
