"""Valida dependencias e comunicacao com os servicos locais, sem criar indices."""
from pathlib import Path
import importlib
import os
import sys

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

packages = ('elasticsearch', 'ollama', 'streamlit', 'fitz', 'pandas', 'dotenv', 'sklearn', 'pytest')
print('Python:', sys.version.split()[0])
for name in packages:
    try:
        importlib.import_module(name)
        print(f'[OK] Biblioteca {name}')
    except ImportError:
        print(f'[ERRO] Biblioteca {name} ausente')

try:
    r = requests.get('http://127.0.0.1:9200', auth=('elastic', os.getenv('ELASTIC_PASSWORD', '')), timeout=8)
    print('[OK] Elasticsearch' if r.ok else f'[ERRO] Elasticsearch HTTP {r.status_code}')
except requests.RequestException as e:
    print('[ERRO] Elasticsearch:', type(e).__name__)

try:
    r = requests.get('http://127.0.0.1:11434/api/tags', timeout=8)
    if r.ok:
        models = [x.get('name', '?') for x in r.json().get('models', [])]
        print('[OK] Ollama. Modelos:', ', '.join(models) if models else '(nenhum)')
    else:
        print('[ERRO] Ollama HTTP', r.status_code)
except requests.RequestException as e:
    print('[ERRO] Ollama:', type(e).__name__)

try:
    r = requests.get('http://127.0.0.1:5601/login', timeout=8)
    print('[OK] Kibana (HTTP {})'.format(r.status_code) if r.status_code < 500 else '[ERRO] Kibana HTTP {}'.format(r.status_code))
except requests.RequestException:
    print('[AVISO] Kibana ainda nao esta disponivel.')
