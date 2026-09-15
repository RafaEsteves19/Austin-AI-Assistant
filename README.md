# Austin

Austin é um assistente pessoal de IA desenvolvido em Python, com uma interface web própria. O projeto combina IA local e via API, memória de conversas, pesquisa na web e uma interface interativa.

## Principais recursos

* Conversação com modelos de IA.
* Suporte a **Groq** e **Ollama**.
* Seleção automática entre modelos/API e execução local.
* Histórico de conversas com **SQLite**.
* Busca de conversas por número, título e linguagem natural.
* Recuperação de conversas e contexto histórico.
* Pesquisa na web com **Tavily**.
* Gerenciamento de sessões e encerramento.
* Respostas em streaming.
* API local com **FastAPI**.
* Interface web com **React + Vite**.
* Esfera visual interativa com **Three.js**.
* Logs e tratamento de erros.
* Redis para serviços auxiliares.
* Docker/WSL para infraestrutura local.

## Tecnologias

**Linguagens:** Python, JavaScript, HTML, CSS e SQL.

**Backend:** Python, FastAPI, SQLite, Redis e WebSocket.

**Frontend:** React, Vite e Three.js.

**IA:** Groq API, Ollama e modelos de linguagem locais.

**Pesquisa:** Tavily Search API.

**Infraestrutura:** Docker, Docker Desktop e WSL 2.

## Estrutura

O projeto separa o núcleo do assistente, IA, histórico, pesquisa, sistema, API e interface web em módulos independentes, permitindo que o Austin continue evoluindo sem concentrar toda a lógica em um único componente.
