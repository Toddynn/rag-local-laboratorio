# Executa todo o roteiro do manual no Windows e gera as evidencias em evidencias\.
# Uso, em um PowerShell comum, na raiz do projeto:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
#   .\scripts\rodar_tudo.ps1
# (a politica vale so para este terminal, como orienta o manual, secao 4.7)

$ErrorActionPreference = 'Continue'
Set-Location (Join-Path $PSScriptRoot '..')
New-Item -ItemType Directory -Force evidencias | Out-Null
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
Start-Transcript -Path evidencias\00_execucao.log -Force | Out-Null

$PY = '.\.venv\Scripts\python.exe'

function Passo($t) { Write-Host ''; Write-Host "=== $(Get-Date -Format HH:mm:ss) $t" }
function Falha($t) { Write-Host "[FALHA] $t"; Stop-Transcript | Out-Null; exit 1 }
function HttpCode($url) {
    try { (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode }
    catch { if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 } }
}

Passo '0. Pre-requisitos'
$pyLauncher = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { $null }
if (-not $pyLauncher) { Falha 'Python nao encontrado (python.org/downloads/windows)' }
Write-Host "[OK] Python: $pyLauncher"
foreach ($c in 'docker', 'ollama') {
    if (Get-Command $c -ErrorAction SilentlyContinue) { Write-Host "[OK] $c" } else { Falha "$c nao encontrado" }
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { Falha 'Docker nao esta rodando. Abra o Docker Desktop e aguarde o status Running.' }
docker run --rm hello-world | Select-Object -First 3

Passo '1. Ambiente virtual e bibliotecas'
if (-not (Test-Path $PY)) { & $pyLauncher -m venv .venv }
& $PY -m pip install -q --upgrade pip
& $PY -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { Falha 'pip install' }
& $PY -c "import sys; print('Interpretador:', sys.executable)"

Passo '2. Credenciais (.env)'
if (Test-Path .env) { Write-Host '.env ja existe; mantido.' } else { & $PY scripts\criar_env.py }

Passo '3. vm.max_map_count (backend WSL 2 do Docker)'
docker run --rm alpine sysctl vm.max_map_count | Tee-Object -FilePath evidencias\vm_max_map_count.txt

Passo '4. Elasticsearch'
docker compose config --quiet
if ($LASTEXITCODE -eq 0) { Write-Host '[OK] compose.yaml valido' }
docker compose up -d elasticsearch
$st = ''
for ($i = 1; $i -le 60; $i++) {
    $st = docker inspect -f '{{.State.Health.Status}}' rag-local-elasticsearch 2>$null
    Write-Host "  saude: $st ($i/60)"
    if ($st -eq 'healthy') { break }
    Start-Sleep 5
}
if ($st -ne 'healthy') { docker compose logs --tail=80 elasticsearch; Falha 'Elasticsearch nao ficou healthy' }

Passo '5. Conta tecnica do Kibana'
& $PY scripts\configurar_kibana.py
if ($LASTEXITCODE -ne 0) { Falha 'configurar_kibana' }

Passo '6. Kibana'
docker compose --profile ui up -d
for ($i = 1; $i -le 60; $i++) {
    $code = HttpCode 'http://127.0.0.1:5601/login'
    Write-Host "  Kibana HTTP $code ($i/60)"
    if ($code -eq 200) { break }
    Start-Sleep 5
}
docker compose --profile ui ps

Passo '7. Ollama e modelos'
if ((HttpCode 'http://127.0.0.1:11434/api/tags') -ne 200) {
    Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden
    Start-Sleep 8
}
ollama --version
ollama pull qwen3:1.7b
ollama pull embeddinggemma
ollama list
ollama run qwen3:1.7b 'Explique em duas frases o que e recuperacao de informacao.' |
    Out-File -Encoding utf8 evidencias\ollama_run_qwen3.txt
Get-Content evidencias\ollama_run_qwen3.txt

Passo '8. Validacao e evidencias'
& $PY scripts\coletar_evidencias.py

Passo '9. Streamlit e capturas de tela'
$proc = Start-Process -FilePath $PY -ArgumentList '-m', 'streamlit', 'run', 'app_teste.py', '--server.headless', 'true', '--server.port', '8501' `
    -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\streamlit.log" -RedirectStandardError "$env:TEMP\streamlit.err"
for ($i = 1; $i -le 30; $i++) { if ((HttpCode 'http://127.0.0.1:8501') -eq 200) { break }; Start-Sleep 2 }
& $PY -m pip install -q playwright
& $PY -m playwright install chromium *> $null
& $PY scripts\capturar_telas.py
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue

Passo '10. Encerramento (sem apagar volumes)'
docker compose --profile ui down 2>&1 | Tee-Object -FilePath evidencias\07_encerramento.txt
docker volume ls | Select-String rag-local | Tee-Object -FilePath evidencias\07_encerramento.txt -Append
ollama stop qwen3:1.7b 2>$null

Passo 'Concluido. Confira a pasta evidencias\.'
Get-ChildItem evidencias
Stop-Transcript | Out-Null
