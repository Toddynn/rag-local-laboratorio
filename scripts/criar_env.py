"""Cria senhas locais para o laboratório, sem sobrescrever um .env existente."""
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.env'
if DEST.exists():
    raise SystemExit('Arquivo .env ja existe. Nenhuma credencial foi alterada.')

values = {
    'STACK_VERSION': '9.5.6',
    'ELASTIC_PASSWORD': secrets.token_urlsafe(24),
    'KIBANA_SYSTEM_PASSWORD': secrets.token_urlsafe(24),
    'KIBANA_ENCRYPTION_KEY': secrets.token_urlsafe(40),
}
content = '\n'.join(f'{key}={value}' for key, value in values.items()) + '\n'
with DEST.open('x', encoding='utf-8') as file:
    file.write(content)
try:
    DEST.chmod(0o600)  # efetivo em Unix; no Windows prevalecem ACLs
except OSError:
    pass
print('Arquivo .env criado no diretorio raiz do projeto.')
print('Guarde as credenciais; nao publique nem compartilhe esse arquivo.')
