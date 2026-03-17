# Contexto: Integrar ZoeBot com a API de automação FBA

O projeto fba-automation (que roda no servidor openclaw-server) tem uma API REST
FastAPI rodando na porta 8001. Essa API já tem um endpoint pronto para receber
comandos de bot. A ZoeBot precisa ser configurada para chamar esse endpoint quando
o usuário enviar comandos relacionados à automação FBA.

## O que a ZoeBot DEVE fazer (e NÃO está fazendo hoje)

Hoje quando o usuário manda "iniciar varrer-fornecedores", a ZoeBot tenta
interpretar como um script shell local ou pergunta detalhes desnecessários
(modo resume/auto). Isso está ERRADO.

O correto é: a ZoeBot deve fazer um POST HTTP para a API do fba-automation
e retornar a resposta ao usuário. Sem perguntar nada. Sem interpretar nada.
Apenas repassar o comando para a API e devolver a reply.

## Endpoint da API

```
POST http://127.0.0.1:8001/api/automation/bot/command
```

(Se o backend FBA rodar em outro IP/host, ajustar o endereço. Na mesma máquina é 127.0.0.1)

### Headers obrigatórios

```
Content-Type: application/json
X-Bot-Token: <valor da env AUTOMATION_BOT_TOKEN configurada no .env.server do fba-automation>
```

Se `AUTOMATION_BOT_ALLOW_UNAUTH=1` estiver setado no servidor, o token não é obrigatório.
Mas é recomendado sempre enviar.

### Body

O payload aceita qualquer um destes campos (a API pega o primeiro que existir):

- `text`
- `message`
- `command`

Exemplo:

```json
{"text": "iniciar varrer-fornecedores"}
```

### Resposta da API

Sempre retorna JSON com:

- `ok` (bool): se o comando foi executado com sucesso
- `reply` (string): mensagem de texto para exibir ao usuário
- Opcionalmente: `profiles`, `status`, `result` com dados extras

## Comandos que a ZoeBot deve reconhecer e repassar

Quando o usuário disser qualquer uma dessas variações, a ZoeBot deve fazer o POST
com o texto correspondente:

| Mensagem do usuário (variações)                       | Texto enviado na API          |
| ----------------------------------------------------- | ----------------------------- |
| "iniciar varrer-fornecedores"                         | `iniciar varrer-fornecedores` |
| "varrer fornecedores" / "varrer-fornecedores"         | `iniciar varrer-fornecedores` |
| "iniciar default-us" / "iniciar clearance-fast" / etc | `iniciar <nome-do-perfil>`    |
| "status automacao" / "como ta a automação?"           | `status automacao`            |
| "parar automacao" / "para a automação"                | `parar automacao`             |
| "listar automacoes" / "quais perfis tem?"             | `listar automacoes`           |
| "ajuda automação"                                     | `ajuda`                       |

A ZoeBot **NÃO** deve perguntar "resume ou auto?", **NÃO** deve mencionar scripts shell,
**NÃO** deve pedir confirmação. Ela apenas faz o POST e retorna a reply da API ao usuário.

## Fluxo completo esperado

1. Usuário manda: "Zoe, iniciar varrer-fornecedores"
2. ZoeBot faz POST para `http://127.0.0.1:8001/api/automation/bot/command`
   com body: `{"text": "iniciar varrer-fornecedores"}`
3. A API internamente:
   - Conecta a VPN automaticamente (`nmcli connection up`)
   - Verifica se o IP é dos EUA
   - Inicia o processo de automação
   - Retorna resposta com PID e status da VPN
4. ZoeBot recebe a resposta e exibe ao usuário, algo como:
   "Automação iniciada com perfil 'varrer-fornecedores' (pid=12345).
   VPN: conectada (US)
   VPN será desconectada automaticamente ao fim da varredura."

## Perfis disponíveis na API (para referência)

- `default-us` — Fluxo padrão US: faixa 0-85, lote 10
- `clearance-fast` — Faixa enxuta para clearance: 10-60
- `premium-scan` — Busca ticket maior: faixa 60-150
- `varrer-fornecedores` — Varre todos os fornecedores com VPN US automática [tem VPN]

## Exemplos de request/response

### Iniciar automação

Request:

```http
POST /api/automation/bot/command
Content-Type: application/json
X-Bot-Token: meu-token-secreto

{"text": "iniciar varrer-fornecedores"}
```

Response (sucesso):

```json
{
  "ok": true,
  "reply": "Automação iniciada com perfil 'varrer-fornecedores' (pid=54321).\nVPN: conectada (US)\nVPN será desconectada automaticamente ao fim da varredura.",
  "result": {"pid": 54321, "profile": "varrer-fornecedores", "vpn": "conectada (US)"}
}
```

Response (já rodando):

```json
{"ok": false, "reply": "Automação já está rodando!"}
```

### Status

Request:

```json
{"text": "status automacao"}
```

Response:

```json
{
  "ok": true,
  "reply": "Automação rodando.\nPerfil: varrer-fornecedores\nPID: 54321\nVPN ativa: Sim\nIniciada em: 2026-03-12 20:45:00",
  "status": {"is_running": true}
}
```

### Parar

Request:

```json
{"text": "parar automacao"}
```

Response:

```json
{"ok": true, "reply": "Automação encerrada (pid=54321)."}
```

### Listar perfis

Request:

```json
{"text": "listar automacoes"}
```

Response:

```json
{
  "ok": true,
  "reply": "Perfis disponíveis:\n- default-us: Fluxo padrão US...\n- varrer-fornecedores [VPN]: Varre todos...",
  "profiles": ["clearance-fast", "default-us", "premium-scan", "varrer-fornecedores"]
}
```

## Resumo do que implementar

1. Criar/registrar o comando "varrer-fornecedores" (e variações) na ZoeBot
2. Quando acionado, fazer POST HTTP para a API (NÃO rodar scripts shell)
3. Incluir o header `X-Bot-Token` com o token configurado
4. Retornar o campo `reply` da resposta como mensagem para o usuário
5. Se `ok` for `false`, tratar como erro e mostrar a reply como mensagem de erro
6. Não perguntar nada ao usuário — a execução é direta, sem confirmação
