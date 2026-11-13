# Laboratório Didático de RAG Local

Atividade da disciplina **Inteligência Artificial** — IFPR União da Vitória (Prof. Me. Jefferson Nogueira de Oliveira).

**Aluno:** Vinicius Gabriel Todis — Tecnologia em Análise e Desenvolvimento de Sistemas

> Esta etapa **não implementa o RAG**. O objetivo é preparar e validar a infraestrutura local
> (Python + Docker + Elasticsearch + Kibana + Ollama + Streamlit) e registrar evidências.
> O indexador e a recuperação híbrida virão nas próximas aulas.

- Manual original: [`docs/manual_rag_local_windows_linux.pdf`](docs/manual_rag_local_windows_linux.pdf)
- Relatório de entrega (evidências + reflexão): [`RELATORIO.md`](RELATORIO.md)

## Arquitetura

```
Pergunta → Python/app → Ollama (embeddinggemma) + Elasticsearch (BM25 + vetores)
         → trechos recuperados + páginas → Ollama (qwen3:1.7b) → resposta com fontes
```

## Estrutura

```
.
├── compose.yaml              # Elasticsearch 9.5.6 + Kibana 9.5.6 (perfil "ui"), só em 127.0.0.1
├── requirements.txt
├── .env.example              # modelo; o .env real é gerado e NÃO é versionado
├── app_teste.py              # interface Streamlit de verificação (não é RAG)
├── scripts/
│   ├── criar_env.py          # gera senhas aleatórias no .env
│   ├── configurar_kibana.py  # define a senha do usuário kibana_system
│   ├── validar_ambiente.py   # testa bibliotecas, Elasticsearch, Ollama e Kibana
│   ├── testar_modelos.py     # chat com qwen3 + embeddings com embeddinggemma
│   └── coletar_evidencias.py # (extra) gera os arquivos da seção 14.2 em evidencias/
├── documentos/               # PDFs das próximas aulas
├── evidencias/               # saídas e capturas de tela para entrega
└── docs/                     # manual em PDF
```

## Passo a passo no macOS (Apple Silicon)

O manual cobre Windows e Linux; no Mac os passos equivalentes são:

| Manual | macOS |
|---|---|
| W1/L1 — identificar sistema | `sw_vers`, `uname -m` (deve dar `arm64`), `sysctl hw.memsize`, `df -h ~` |
| W2/L2 — Python e VS Code | `brew install python@3.12` · VS Code + extensão Python |
| W3 — WSL 2 | não se aplica |
| W4/L3/L4 — Docker | Docker Desktop for Mac (Apple Silicon). Sem `sudo` |
| W5/L5 — `vm.max_map_count` | gerenciado pela VM do Docker Desktop; conferir com `docker run --rm --privileged alpine sysctl vm.max_map_count` |
| W6/L6 — Ollama | app de ollama.com/download ou `brew install ollama` |

As imagens oficiais da Elastic são multi-arquitetura, então rodam nativamente em ARM.

```bash
# 1. Ambiente virtual e bibliotecas
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# 2. Credenciais locais (uma vez só; não regenerar com o volume já criado)
./.venv/bin/python scripts/criar_env.py

# 3. Elasticsearch
docker compose config --quiet
docker compose up -d elasticsearch
docker compose ps                      # aguardar "healthy"

# 4. Conta técnica do Kibana e subir o Kibana
./.venv/bin/python scripts/configurar_kibana.py
docker compose --profile ui up -d      # abrir http://127.0.0.1:5601 (usuário elastic)

# 5. Modelos
ollama pull qwen3:1.7b
ollama pull embeddinggemma
ollama run qwen3:1.7b                  # "Explique em duas frases o que e recuperacao de informacao."  /bye

# 6. Validação e evidências
./.venv/bin/python scripts/validar_ambiente.py
./.venv/bin/python scripts/testar_modelos.py
./.venv/bin/python scripts/coletar_evidencias.py

# 7. Streamlit (print para evidencias/05_streamlit.png)
./.venv/bin/python -m streamlit run app_teste.py   # http://127.0.0.1:8501

# 8. Encerrar SEM apagar volumes (nunca usar -v por rotina)
docker compose --profile ui down
ollama stop qwen3:1.7b
```

### Execução automática

| Sistema | Comando (na raiz do projeto) |
|---|---|
| macOS / Ubuntu / Debian | `bash scripts/rodar_tudo.sh` (no Linux, usa `sudo docker` quando o usuário não está no grupo `docker`) |
| Windows (PowerShell comum) | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` e depois `.\scripts\rodar_tudo.ps1` |

Os dois scripts seguem a ordem do manual e gravam tudo em `evidencias/`, incluindo o log `00_execucao.log`.

## Segurança

- `.env` e `.venv/` estão no `.gitignore` — nunca commitar senhas.
- Portas publicadas apenas em `127.0.0.1`; não reutilizar esta configuração em produção.
- `kibana_system` é conta técnica; o login humano é `elastic`.
- Capturas de tela não devem mostrar o `.env`.
