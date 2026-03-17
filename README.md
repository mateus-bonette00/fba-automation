# FBA Automation (Official)

Projeto principal para captura de abas, scraping de fornecedor e automacao FBA.

## Fluxo oficial (Linux)

```bash
chmod +x iniciar_tudo.sh
./iniciar_tudo.sh
```

Esse script sobe:
- Opera Debug em `http://localhost:9222`
- Backend em `http://localhost:8001`
- Frontend em `http://localhost:5173`

## URLs principais

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/health`

## Automacao completa

Detalhes da automacao por planilha, parametros e execucao:

- [AUTOMATION.md](AUTOMATION.md)
- [DEPLOY_OPENCLAW_SERVER.md](DEPLOY_OPENCLAW_SERVER.md)

## Captura manual (opcional)

Se quiser usar Chrome em modo debug manualmente:

```bash
./iniciar_chrome_debug.sh
```

Se quiser subir Opera debug separadamente:

```bash
./iniciar_opera_debug.sh
```

## Windows

Guia de uso em Windows:

- [README-WINDOWS.md](README-WINDOWS.md)
