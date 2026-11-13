"""Coleta as evidencias da secao 14.2 do manual em evidencias/.

Uso (na raiz do projeto, com Elasticsearch/Kibana/Ollama ja rodando):
    ./.venv/bin/python scripts/coletar_evidencias.py

Nao le nem grava o conteudo do .env. As capturas de tela (Kibana e
Streamlit) precisam ser feitas manualmente.
"""
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidencias'
OUT.mkdir(exist_ok=True)


def run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip() or '(sem saida)'
    except FileNotFoundError:
        return f'(comando nao encontrado: {cmd[0]})'
    except subprocess.TimeoutExpired:
        return f'(tempo esgotado apos {timeout}s)'


def save(name, text):
    (OUT / name).write_text(text + '\n', encoding='utf-8')
    print(f'[OK] evidencias/{name}')


# 1. Identificacao da estacao
system = platform.system()
info = [
    f'Sistema: {platform.platform()}',
    f'Arquitetura: {platform.machine()}',
    f'Python: {sys.version.split()[0]} ({sys.executable})',
]
if system == 'Darwin':
    info.append('macOS: ' + run(['sw_vers']).replace('\n', ' | '))
    mem = run(['sysctl', '-n', 'hw.memsize'])
    if mem.isdigit():
        info.append(f'RAM: {int(mem) / 1024**3:.1f} GB')
    info.append('CPU: ' + run(['sysctl', '-n', 'machdep.cpu.brand_string']))
elif system == 'Linux':
    info.append(run(['cat', '/etc/os-release']))
    info.append(run(['free', '-h']))
else:
    info.append(run(['cmd', '/c', 'ver']))
total, used, free = shutil.disk_usage(ROOT)
info.append(f'Disco livre: {free / 1024**3:.1f} GB de {total / 1024**3:.1f} GB')
info.append('Docker: ' + run(['docker', '--version']))
info.append('Compose: ' + run(['docker', 'compose', 'version']))
info.append('Ollama: ' + run(['ollama', '--version']))
save('01_estacao.txt', '\n'.join(info))

# 2. docker compose ps
save('02_docker_compose_ps.txt', run(['docker', 'compose', '--profile', 'ui', 'ps']))

# 3 e 4. Scripts de validacao
save('03_validar_ambiente.txt', run([sys.executable, 'scripts/validar_ambiente.py']))
save('04_testar_modelos.txt', run([sys.executable, 'scripts/testar_modelos.py'], timeout=600))

# 6. Versoes instaladas (o manual pede este nome de arquivo)
freeze = run([sys.executable, '-m', 'pip', 'freeze'])
(ROOT / 'versoes-instaladas.txt').write_text(freeze + '\n', encoding='utf-8')
save('06_versoes-instaladas.txt', freeze)

save('ollama_list.txt', run(['ollama', 'list']))

print('\nFaltam as capturas manuais:')
print('  evidencias/02_kibana.png    -> http://127.0.0.1:5601 logado como elastic')
print('  evidencias/05_streamlit.png -> http://127.0.0.1:8501 apos clicar no botao')
print('Revise os arquivos antes de commitar: nenhum deve conter senha.')
