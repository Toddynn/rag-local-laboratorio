"""Captura as telas pedidas na secao 14.2 (Kibana autenticado e Streamlit).

Requer: pip install playwright && python -m playwright install chromium
A senha e lida do .env e digitada no campo de senha; nunca e impressa.
"""
from pathlib import Path
import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidencias'
OUT.mkdir(exist_ok=True)
load_dotenv(ROOT / '.env')

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)

    # Kibana: login com o usuario elastic
    try:
        page.goto('http://127.0.0.1:5601/login', timeout=120_000)
        page.locator('[data-test-subj="loginUsername"]').fill('elastic', timeout=120_000)
        page.locator('[data-test-subj="loginPassword"]').fill(os.environ['ELASTIC_PASSWORD'])
        page.locator('[data-test-subj="loginSubmit"]').click()
        page.wait_for_url(lambda url: '/login' not in url, timeout=120_000)
        page.goto('http://127.0.0.1:5601/app/management/data/index_management/indices', timeout=120_000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / '02_kibana.png'))
        print('[OK] evidencias/02_kibana.png')
    except Exception as e:  # noqa: BLE001
        print('[ERRO] Kibana:', type(e).__name__, str(e)[:200])

    # Streamlit: digita a pergunta e clica no botao
    try:
        page.goto('http://127.0.0.1:8501', timeout=60_000)
        page.get_by_role('button', name='Verificar interface').click(timeout=60_000)
        page.get_by_text('Interface pronta').wait_for(timeout=30_000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(OUT / '05_streamlit.png'))
        print('[OK] evidencias/05_streamlit.png')
    except Exception as e:  # noqa: BLE001
        print('[ERRO] Streamlit:', type(e).__name__, str(e)[:200])

    browser.close()
