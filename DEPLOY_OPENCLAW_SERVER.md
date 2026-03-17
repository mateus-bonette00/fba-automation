# Deploy Completo no `openclaw-server` + ZoeBot (OpenClaw)

Tutorial de ponta a ponta para:
- publicar o `fba-automation` no servidor;
- Chrome Debug com anti-deteccao rodando automaticamente;
- VPN liga/desliga automaticamente por perfil;
- controlar tudo via ZoeBot com comando por texto;
- nenhuma intervencao manual necessaria apos setup.

---

## 0) Antes de comecar

### 0.1 O que voce precisa

| Item | Valor |
|------|-------|
| Acesso SSH | `ssh openclaw-server` |
| Projeto local | `/home/mateus/Documentos/Qota Store/codigos/fba-automation` |
| Usuario remoto | `bonette` |
| Pasta no servidor | `~/apps/fba-automation` |
| VPN no servidor | `usa-newyork-udp` (via nmcli) |
| Navegador no servidor | Google Chrome (nao Opera) |

### 0.2 Onde executar cada comando

- **LOCAL**: seu notebook/PC.
- **SERVIDOR**: shell dentro de `ssh openclaw-server`.

---

## 1) Publicar o projeto no servidor

### 1.1 (LOCAL) Enviar arquivos com `rsync`

```bash
rsync -av --delete \
  --exclude '/.git/***' \
  --exclude '/backend/venv/***' \
  --exclude '/frontend/node_modules/***' \
  --exclude '__pycache__/***' \
  --exclude '*.pyc' \
  --exclude '/logs/***' \
  --exclude '/exports/***' \
  --exclude '.env.local' \
  --exclude '.env.server' \
  "/home/mateus/Documentos/Qota Store/códigos/fba-automation/" \
  openclaw-server:~/apps/fba-automation/
```

### 1.2 (SERVIDOR) Confirmar pasta

```bash
ssh openclaw-server
cd ~/apps/fba-automation
ls -la
```

---

## 2) Instalar ambiente Python no servidor

### 2.1 (SERVIDOR) Criar venv e instalar dependencias

```bash
cd ~/apps/fba-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pandas python-multipart google-api-python-client google-auth-httplib2 google-auth-oauthlib
python -m playwright install chromium
```

### 2.2 (SERVIDOR) Verificacao rapida

```bash
python -V
pip -V
```

---

## 3) Instalar Google Chrome no servidor

O servidor usa Chrome em vez de Opera. Se ainda nao tem Chrome instalado:

### 3.1 (SERVIDOR) Instalar Chrome

```bash
# Opcao A: Google Chrome (recomendado)
wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i /tmp/chrome.deb
sudo apt-get install -f -y
rm /tmp/chrome.deb

# Opcao B: Chromium (se preferir)
sudo apt install -y chromium-browser
```

### 3.2 (SERVIDOR) Verificar instalacao

```bash
google-chrome --version
```

---

## 4) Variaveis de ambiente

### 4.1 Onde criar

No servidor, na **raiz do projeto** (nao mais dentro de `backend/`):

`~/apps/fba-automation/.env.server`

O script `iniciar_tudo_servidor.sh` carrega este arquivo automaticamente.

### 4.2 (SERVIDOR) Gerar token forte

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o token gerado.

### 4.3 (SERVIDOR) Criar o `.env.server`

```bash
cd ~/apps/fba-automation
nano .env.server
```

Cole este conteudo (substitua `SEU_TOKEN_AQUI`):

```env
# === Autenticacao do Bot ===
AUTOMATION_BOT_TOKEN=SEU_TOKEN_AQUI
AUTOMATION_BOT_ALLOW_UNAUTH=0

# === Paths ===
AUTOMATION_PROFILES_FILE=/home/bonette/apps/fba-automation/backend/config/automation_profiles.json

# === Protecao de stop acidental ===
AUTOMATION_STOP_PROTECTION=0

# === Chrome no servidor ===
# CHROME_BIN=/usr/bin/google-chrome-stable   # descomente se auto-deteccao falhar
CHROME_HEADLESS=1
CHROME_AUTOMATION_USER_DATA_DIR=/home/bonette/chrome-automation

# === Performance (opcional, o script tem defaults) ===
# AUTOMATION_PERFORMANCE_PROFILE=super-estavel
```

Salvar: `Ctrl+O`, Enter, `Ctrl+X`

### 4.4 (SERVIDOR) Confirmar

```bash
cat ~/apps/fba-automation/.env.server
```

---

## 5) Primeiro teste manual

### 5.1 (SERVIDOR) Iniciar tudo com o script

```bash
cd ~/apps/fba-automation
./iniciar_tudo_servidor.sh super-estavel
```

O script vai:
1. Detectar o Chrome automaticamente
2. Iniciar Chrome Debug na porta 9222 (headless)
3. Ativar watchdog (reinicia Chrome se cair)
4. Subir o backend na porta 8001
5. Mostrar resumo e ficar monitorando logs

### 5.2 (SERVIDOR - outro terminal) Validar

```bash
# Health check
curl -s http://127.0.0.1:8001/api/health

# Listar perfis
curl -s http://127.0.0.1:8001/api/automation/profiles

# Testar endpoint do bot
curl -s -X POST http://127.0.0.1:8001/api/automation/bot/command \
  -H "Content-Type: application/json" \
  -H "x-bot-token: SEU_TOKEN_AQUI" \
  -d '{"text":"listar automacoes"}'

# Verificar Chrome Debug
curl -s http://127.0.0.1:9222/json/version
```

Respostas esperadas:
```json
{"status":"ok","message":"Backend rodando"}
```

### 5.3 Para encerrar o teste

`Ctrl+C` no terminal do script. Ele mata tudo (Chrome, backend, orfaos).

---

## 6) Rodar como servico permanente (systemd)

Isso faz o sistema subir sozinho quando o servidor ligar e reiniciar automaticamente se crashar. **Voce nunca mais precisa fazer SSH para iniciar.**

### 6.1 (SERVIDOR) Criar servico

```bash
sudo tee /etc/systemd/system/fba-automation.service > /dev/null <<'EOF'
[Unit]
Description=FBA Automation (Chrome + Backend)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=bonette
WorkingDirectory=/home/bonette/apps/fba-automation
EnvironmentFile=/home/bonette/apps/fba-automation/.env.server
ExecStart=/home/bonette/apps/fba-automation/iniciar_tudo_servidor.sh super-estavel
Restart=always
RestartSec=10
Environment=CHROME_HEADLESS=1

[Install]
WantedBy=multi-user.target
EOF
```

### 6.2 (SERVIDOR) Ativar

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fba-automation
sudo systemctl status fba-automation
```

### 6.3 Comandos uteis

```bash
# Ver status
sudo systemctl status fba-automation

# Reiniciar (ex: apos atualizar codigo)
sudo systemctl restart fba-automation

# Parar
sudo systemctl stop fba-automation

# Logs ao vivo
sudo journalctl -u fba-automation -f

# Logs do backend
tail -f ~/apps/fba-automation/logs/backend.log

# Logs do Chrome watchdog
tail -f ~/apps/fba-automation/logs/chrome_watchdog.log

# Logs de diagnostico da automacao
tail -f ~/apps/fba-automation/backend/logs/automation_diagnostics.jsonl
```

---

## 7) VPN automatica por perfil

A VPN e gerenciada **automaticamente** pela API. Nao precisa ligar/desligar manualmente.

### 7.1 Como funciona

O perfil `varrer-fornecedores` no `automation_profiles.json` tem:

```json
"vpn_up": "nmcli connection up id 'usa-newyork-udp'",
"vpn_down": "nmcli connection down id 'usa-newyork-udp'",
"vpn_verify_country": "US"
```

Quando a ZoeBot envia `"iniciar varrer-fornecedores"`:

1. Backend executa `nmcli connection up id 'usa-newyork-udp'`
2. Verifica se IP publico esta nos US (5 tentativas)
3. Inicia o robo `run_automation.py`
4. Thread em background monitora o processo
5. Quando o robo termina (sucesso ou falha) → executa `nmcli connection down id 'usa-newyork-udp'`
6. Se o usuario pedir "parar automacao", a VPN tambem desconecta

### 7.2 (SERVIDOR) Verificar VPN disponivel

```bash
# Listar conexoes VPN configuradas
nmcli connection show | grep vpn

# Testar manualmente
nmcli connection up id 'usa-newyork-udp'
curl -s https://ipapi.co/country/
nmcli connection down id 'usa-newyork-udp'
```

### 7.3 Perfis sem VPN

Os perfis `default-us`, `clearance-fast` e `premium-scan` nao tem VPN configurada. Eles iniciam a automacao direto, sem mexer na rede. Use eles para testes locais ou quando a VPN ja estiver conectada manualmente.

---

## 8) Perfis de automacao

Arquivo: `~/apps/fba-automation/backend/config/automation_profiles.json`

### 8.1 Perfis disponiveis

| Perfil | Descricao | Preco | VPN |
|--------|-----------|-------|-----|
| `varrer-fornecedores` | Varredura padrao completa | $0-$85 | Sim (US) |
| `default-us` | Mesmo que acima, sem VPN | $0-$85 | Nao |
| `clearance-fast` | Faixa enxuta clearance | $10-$60 | Nao |
| `premium-scan` | Ticket alto | $60-$150 | Nao |

### 8.2 Editar perfis

```bash
nano ~/apps/fba-automation/backend/config/automation_profiles.json
```

Nao precisa reiniciar o backend. Os perfis sao lidos do disco a cada chamada.

### 8.3 Adicionar VPN a qualquer perfil

Adicione estas chaves ao perfil desejado:

```json
"vpn_up": "nmcli connection up id 'usa-newyork-udp'",
"vpn_down": "nmcli connection down id 'usa-newyork-udp'",
"vpn_verify_country": "US"
```

---

## 9) Endpoints da API (referencia para ZoeBot)

Base: `http://127.0.0.1:8001/api/automation`

### 9.1 Comando textual (modo ideal para ZoeBot)

```bash
curl -s -X POST http://127.0.0.1:8001/api/automation/bot/command \
  -H "Content-Type: application/json" \
  -H "x-bot-token: SEU_TOKEN_AQUI" \
  -d '{"text":"iniciar varrer-fornecedores"}'
```

Comandos aceitos no `text`:

| Comando | O que faz |
|---------|-----------|
| `listar automacoes` | Lista perfis disponiveis |
| `iniciar varrer-fornecedores` | Liga VPN + inicia varredura |
| `iniciar <perfil>` | Inicia qualquer perfil |
| `status automacao` | Mostra estado atual (rodando/parado, VPN, PID) |
| `parar automacao` | Para a automacao (VPN desconecta automaticamente) |
| `ajuda` | Lista todos os comandos |

### 9.2 Endpoints REST diretos

```bash
# Listar perfis
curl -s http://127.0.0.1:8001/api/automation/profiles

# Iniciar perfil diretamente
curl -s -X POST http://127.0.0.1:8001/api/automation/start-profile/varrer-fornecedores

# Status
curl -s http://127.0.0.1:8001/api/automation/status

# Parar
curl -s -X POST "http://127.0.0.1:8001/api/automation/stop?force=true"

# Logs (ultimas 50 linhas)
curl -s "http://127.0.0.1:8001/api/automation/logs?lines=50"

# Health check
curl -s http://127.0.0.1:8001/api/health
```

---

## 10) Fluxo completo da ZoeBot

```
Usuario: "Zoe, varrer fornecedores"

ZoeBot:
  1. POST /api/automation/bot/command {"text": "iniciar varrer-fornecedores"}

Servidor (automatico):
  2. nmcli connection up id 'usa-newyork-udp'     → VPN liga
  3. Verifica IP publico = US                       → confirma
  4. python3 run_automation.py --resume ...          → robo inicia
  5. [thread monitora processo em background]

  ... robo varre todos os fornecedores da planilha ...
  ... exporta XLSX a cada 500 produtos ...

  6. Robo termina (todos fornecedores processados)
  7. nmcli connection down id 'usa-newyork-udp'    → VPN desliga

ZoeBot pode consultar progresso a qualquer momento:
  POST /api/automation/bot/command {"text": "status automacao"}
```

### 10.1 Se o usuario quiser parar no meio

```
Usuario: "Zoe, parar automacao"
ZoeBot: POST /api/automation/bot/command {"text": "parar automacao"}
Servidor: mata o robo + desconecta VPN
```

---

## 11) Operacao diaria

### 11.1 Atualizar projeto no servidor

(LOCAL)

```bash
rsync -av --delete \
  --exclude '/.git/***' \
  --exclude '/backend/venv/***' \
  --exclude '/frontend/node_modules/***' \
  --exclude '__pycache__/***' \
  --exclude '*.pyc' \
  --exclude '/logs/***' \
  --exclude '/exports/***' \
  --exclude '.env.local' \
  --exclude '.env.server' \
  "/home/mateus/Documentos/Qota Store/códigos/fba-automation/" \
  openclaw-server:~/apps/fba-automation/
```

(SERVIDOR)

```bash
source ~/apps/fba-automation/.venv/bin/activate
pip install -r ~/apps/fba-automation/requirements.txt
sudo systemctl restart fba-automation
```

### 11.2 Ver logs

```bash
# Backend
sudo journalctl -u fba-automation -f

# Automacao
tail -f ~/apps/fba-automation/logs/backend.log

# Diagnostico detalhado
tail -f ~/apps/fba-automation/backend/logs/automation_diagnostics.jsonl
```

### 11.3 Ver exports gerados

```bash
ls -la ~/apps/fba-automation/backend/exports/ARQUIVOS\ XLSX/Mateus/
```

### 11.4 Baixar exports para o notebook

(LOCAL)

```bash
rsync -av openclaw-server:~/apps/fba-automation/backend/exports/ \
  "/home/mateus/Documentos/Qota Store/códigos/fba-automation/backend/exports/"
```

---

## 12) Problemas comuns

### Chrome nao encontrado

```
Nenhum Google Chrome ou Chromium encontrado no sistema.
```
- Solucao: instalar Chrome (secao 3) ou definir `CHROME_BIN` no `.env.server`.

### Chrome nao inicia (headless sem display)

```
Falha ao conectar no Chrome debug (9222).
```
- Verificar: `CHROME_HEADLESS=1` no `.env.server`
- Ver log: `tail -n 50 ~/apps/fba-automation/logs/chrome_debug.log`

### VPN falha ao conectar

```
Falha ao conectar VPN: ...
```
- Verificar se a conexao existe: `nmcli connection show | grep usa-newyork`
- Testar manualmente: `nmcli connection up id 'usa-newyork-udp'`
- Se o nome mudou, editar `vpn_up`/`vpn_down` no `automation_profiles.json`

### IP nao esta nos US apos VPN

```
VPN conectou mas IP nao esta em US
```
- VPN pode estar lenta. Aumentar timeout no `.env.server`:
  `VPN_VERIFY_ATTEMPTS=8`
- Ou o servidor VPN saiu do US. Testar: `curl https://ipapi.co/country/`

### Porta 8001 ocupada

```
Porta 8001 ocupada por outro projeto.
```
- O script tenta liberar automaticamente.
- Se persistir: `lsof -ti:8001 | xargs kill -9`

### Porta 9222 ocupada

```
Porta 9222 ocupada por processo que nao e Chrome Debug.
```
- O script tenta liberar automaticamente.
- Se persistir: `lsof -ti:9222 | xargs kill -9`

### Endpoint do bot retorna `AUTOMATION_BOT_TOKEN nao configurado`

- Causa: backend iniciado sem `.env.server`.
- Se usando systemd: verificar `EnvironmentFile` no service.
- Se manual: `set -a; source .env.server; set +a` antes de iniciar.

### Timeout ao acessar servidor do notebook

- Usar tunel SSH:
```bash
ssh -L 18001:127.0.0.1:8001 openclaw-server
# Depois no local:
curl -s http://127.0.0.1:18001/api/health
```

---

## 13) Checklist final

- [ ] Chrome instalado no servidor (`google-chrome --version`)
- [ ] Projeto sincronizado em `~/apps/fba-automation`
- [ ] `.venv` criado e dependencias instaladas
- [ ] `.env.server` criado na raiz do projeto com token
- [ ] VPN testada: `nmcli connection up/down id 'usa-newyork-udp'`
- [ ] Teste manual OK: `./iniciar_tudo_servidor.sh super-estavel`
- [ ] `GET /api/health` respondendo
- [ ] `POST /api/automation/bot/command` respondendo com token
- [ ] Servico systemd criado e ativo (`fba-automation.service`)
- [ ] ZoeBot chamando endpoint com `x-bot-token`
- [ ] Testar fluxo completo: "iniciar varrer-fornecedores" via bot
