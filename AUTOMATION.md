# Guia de Automação de Fornecedores FBA

Este projeto automatiza a captura de produtos diretamente do navegador (Chrome/Opera via CDP), filtrando por limite de preço ($75) e iterando as páginas e fornecedores automaticamente usando os dados da planilha Google Sheets. A automação também exporta tudo num formato XLSX idêntico à sua planilha de referência.

## 1. Pré-Requisitos

A automação foi criada em Python utilizando Playwright para conectar a um navegador já aberto.
Antes de começar, certifique-se de que os pacotes do Python estão instalados. Dentro da pasta `backend`:

```bash
cd backend
./venv/bin/pip install openpyxl google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

> [!WARNING]
> Como esta ferramenta roda em cima de navegadores reais, você **deve** iniciar o seu Chrome/Opera com a porta de debug ativada. Pode-se usar o existente `iniciar_chrome_debug.sh` ou similar. O script tentará conectar em `http://127.0.0.1:9222`.

## 2. Como Rodar

Abra um terminal (`backend/`) e execute a automação principal:

```bash
./venv/bin/python run_automation.py
```

### Argumentos de Configuração

Você pode ajustar os limites passando parâmetros. Exemplos:

- Mudar o batch size (padrão é 20):
  `./venv/bin/python run_automation.py --batch-size 15`
- Mudar limite de preço:
  `./venv/bin/python run_automation.py --price-limit 50.0`
  _Passando 0 ignora o limite de preço._

- Mudar a quantidade de produtos acumulados até forçar o download (padrão 500):
  `./venv/bin/python run_automation.py --export-threshold 300`

### Como a automação funciona na prática:

1. **Leitura da Planilha**: Pega o próximo fornecedor válido pela coluna `INDICE` e link HTTP.
2. **Navegação**: Abre o fornecedor na tela, e começa as paginações através dos botões _Next_.
3. **Coleta e Captura**: Extrai links menores ou iguais a $75, abre esses links como abas, dispara seu `/api/capture/capture-tabs` para extrair os UPCs/Títulos.
4. **Acúmulo e Exportação**: Manda os dados num XLS formatado exatamente como a sua amostra e fecha as abas antigas para salvar RAM.
5. Ao concluir as páginas, finaliza o output e segue para o próximo fornecedor. Retoma caso caia ou você interromper (há o arquivo `automation_state.json`).

> [!NOTE]
> Se houver CAPTCHAs, a ferramenta irá pausar, alertá-lo no terminal e aguardará que você digite a tecla ENTER após resolver a verificação visual no browser.

## 3. Leitura da Planilha (sem coluna FEITO/VISTO)

A automação acessa a planilha via exportação pública CSV (somente leitura) e **não depende de coluna `FEITO`/`VISTO`**.

O controle de progresso é interno, via arquivo de estado:
- `backend/automation_state.json`
- `processed_suppliers_indices`
- `deferred_suppliers_indices`
