"""Define a senha interna do usuario kibana_system via API do Elasticsearch."""
from pathlib import Path
import sys
import time

import requests
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
password = os.getenv('ELASTIC_PASSWORD')
kibana_password = os.getenv('KIBANA_SYSTEM_PASSWORD')
if not password or not kibana_password:
    raise SystemExit('Faltam senhas no .env. Execute criar_env.py.')

url = 'http://127.0.0.1:9200/_security/user/kibana_system/_password'
for attempt in range(1, 16):
    try:
        response = requests.post(
            url,
            auth=('elastic', password),
            json={'password': kibana_password},
            timeout=10,
        )
        if response.status_code == 200:
            print('Senha interna do Kibana configurada com sucesso.')
            sys.exit(0)
        if response.status_code == 401:
            raise SystemExit('Autenticacao falhou. Confira se as credenciais correspondem ao volume do Elasticsearch.')
        raise SystemExit(f'Falha HTTP {response.status_code}: {response.text[:300]}')
    except requests.ConnectionError:
        print(f'Elasticsearch ainda indisponivel: tentativa {attempt}/15')
        time.sleep(3)
raise SystemExit('Elasticsearch nao respondeu em http://127.0.0.1:9200')
