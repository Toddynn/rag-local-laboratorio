#!/usr/bin/env bash
# Executa todo o roteiro do manual (macOS/Linux) e gera as evidencias em evidencias/.
# Uso, na raiz do projeto:  bash scripts/rodar_tudo.sh
set -u
cd "$(dirname "$0")/.."
mkdir -p evidencias
LOG=evidencias/00_execucao.log
exec > >(tee "$LOG") 2>&1

PY=./.venv/bin/python
DC="docker compose"
if [ "$(uname)" = "Linux" ] && ! docker info >/dev/null 2>&1; then DC="sudo docker compose"; fi

passo() { echo; echo "=== $(date '+%H:%M:%S') $*"; }
falha() { echo "[FALHA] $*"; exit 1; }

passo "0. Pre-requisitos"
for c in python3 docker ollama curl; do
  command -v "$c" >/dev/null && echo "[OK] $c: $(command -v "$c")" || falha "$c nao encontrado (macOS: brew install $c / Docker Desktop / ollama.com/download)"
done
docker info >/dev/null 2>&1 || falha "Docker nao esta rodando. Abra o Docker Desktop."
docker run --rm hello-world | head -3

passo "1. Ambiente virtual e bibliotecas"
[ -d .venv ] || python3 -m venv .venv
$PY -m pip install -q --upgrade pip
$PY -m pip install -q -r requirements.txt || falha "pip install"
$PY -c "import sys; print('Interpretador:', sys.executable)"

passo "2. Credenciais (.env)"
[ -f .env ] && echo ".env ja existe; mantido." || $PY scripts/criar_env.py

passo "3. vm.max_map_count (VM do Docker)"
docker run --rm alpine sysctl vm.max_map_count | tee evidencias/vm_max_map_count.txt

passo "4. Elasticsearch"
$DC config --quiet && echo "[OK] compose.yaml valido"
$DC up -d elasticsearch
for i in $(seq 1 60); do
  st=$(docker inspect -f '{{.State.Health.Status}}' rag-local-elasticsearch 2>/dev/null)
  echo "  saude: $st ($i/60)"; [ "$st" = "healthy" ] && break; sleep 5
done
[ "$st" = "healthy" ] || { $DC logs --tail=80 elasticsearch; falha "Elasticsearch nao ficou healthy"; }

passo "5. Conta tecnica do Kibana"
$PY scripts/configurar_kibana.py || falha "configurar_kibana"

passo "6. Kibana"
$DC --profile ui up -d
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5601/login)
  echo "  Kibana HTTP $code ($i/60)"; [ "$code" = "200" ] && break; sleep 5
done
$DC --profile ui ps

passo "7. Ollama e modelos"
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null; then
  (open -a Ollama 2>/dev/null || (nohup ollama serve >/tmp/ollama.log 2>&1 &)); sleep 8
fi
ollama --version
ollama pull qwen3:1.7b
ollama pull embeddinggemma
ollama list
echo "Explique em duas frases o que e recuperacao de informacao." > /tmp/pergunta.txt
ollama run qwen3:1.7b "$(cat /tmp/pergunta.txt)" < /dev/null | tee evidencias/ollama_run_qwen3.txt

passo "8. Validacao e evidencias"
$PY scripts/coletar_evidencias.py

passo "9. Streamlit e capturas de tela"
$PY -m streamlit run app_teste.py --server.headless true --server.port 8501 > /tmp/streamlit.log 2>&1 &
ST_PID=$!
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8501 && break; sleep 2; done
$PY -m pip install -q playwright && $PY -m playwright install chromium >/dev/null 2>&1
$PY scripts/capturar_telas.py
kill $ST_PID 2>/dev/null

passo "10. Encerramento (sem apagar volumes)"
$DC --profile ui down 2>&1 | tee evidencias/07_encerramento.txt
docker volume ls | grep rag-local | tee -a evidencias/07_encerramento.txt
ollama stop qwen3:1.7b 2>/dev/null

passo "Concluido. Confira a pasta evidencias/."
ls -la evidencias
