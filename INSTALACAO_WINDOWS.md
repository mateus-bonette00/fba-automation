# 🪟 Instalação Completa - Windows

Este guia explica como instalar e rodar o projeto FBA Automation em uma máquina Windows **do zero**, sem precisar ter nada instalado previamente.

---

## 📋 Pré-requisitos

- Windows 10 ou superior
- Conexão com a internet
- Permissões de Administrador

---

## 🚀 Instalação Automática (Recomendado)

### Opção 1: Script PowerShell (Mais Completo)

1. **Baixe o projeto** ou navegue até a pasta do projeto

2. **Clique com botão direito** no arquivo `instalar_windows.ps1`

3. Selecione **"Executar com PowerShell"**

4. Se aparecer erro de permissão, execute:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   ```
   E depois execute o script novamente

5. **Siga as instruções na tela**

O script irá instalar automaticamente:
- ✅ Chocolatey (gerenciador de pacotes)
- ✅ Python 3.11
- ✅ Node.js 20 LTS
- ✅ Google Chrome
- ✅ Git
- ✅ Todas as dependências do projeto
- ✅ Criar scripts de inicialização

**Tempo estimado**: 10-15 minutos (dependendo da internet)

---

## 📦 O que é instalado?

### 1. **Chocolatey**
Gerenciador de pacotes para Windows (como apt no Linux)

### 2. **Python 3.11**
Linguagem necessária para o backend
- Instalado em: `C:\Python311`
- pip (gerenciador de pacotes Python)

### 3. **Node.js 20 LTS**
Necessário para o frontend React
- npm (gerenciador de pacotes Node)

### 4. **Google Chrome**
Navegador necessário para captura de produtos
- Instalado em: `C:\Program Files\Google\Chrome`

### 5. **Git**
Sistema de controle de versão

### 6. **Dependências Python**
- FastAPI (framework web)
- Playwright (automação de navegador)
- BeautifulSoup4 (parsing HTML)
- Requests/HTTPX (requisições HTTP)
- E outras...

### 7. **Dependências Node.js**
- React (framework frontend)
- Vite (build tool)
- React Router (navegação)
- E outras...

---

## 🎯 Como Usar Após Instalação

### Iniciar o Sistema Completo

Execute o arquivo:
```
iniciar_tudo.bat
```

Isso irá abrir **3 janelas**:
1. **Chrome Debug** (janela roxa) - Use este para abrir produtos
2. **Backend** (servidor Python na porta 8001)
3. **Frontend** (interface React na porta 5173)

### Acessar o Sistema

Abra seu navegador normal em:
```
http://localhost:5173
```

### Capturar Produtos

1. No **Chrome Debug** (janela roxa), abra as páginas dos produtos
2. No navegador normal, acesse: `http://localhost:5173/capture`
3. Clique em "Capturar Abas"
4. Os produtos serão extraídos automaticamente

---

## 🛠️ Instalação Manual (Se o script falhar)

### 1. Instalar Python 3.11

1. Baixe em: https://www.python.org/downloads/
2. **IMPORTANTE**: Marque "Add Python to PATH" durante instalação
3. Instale normalmente

Verifique:
```cmd
python --version
```

### 2. Instalar Node.js 20 LTS

1. Baixe em: https://nodejs.org/
2. Instale a versão LTS (recomendada)

Verifique:
```cmd
node --version
npm --version
```

### 3. Instalar Google Chrome

1. Baixe em: https://www.google.com/chrome/
2. Instale normalmente

### 4. Instalar Dependências Python

Abra o **PowerShell** na pasta do projeto:

```powershell
# Criar virtual environment
python -m venv backend\venv

# Ativar virtual environment
backend\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar navegadores Playwright
python -m playwright install chromium
```

### 5. Instalar Dependências Node.js

```cmd
cd frontend
npm install
cd ..
```

---

## 🚦 Iniciar Manualmente

### Backend (Terminal 1)
```cmd
cd backend
venv\Scripts\activate
python main.py
```

### Frontend (Terminal 2)
```cmd
cd frontend
npm run dev
```

### Chrome Debug (Terminal 3)
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug"
```

---

## ❓ Problemas Comuns

### Erro: "python não é reconhecido"
**Solução**: Python não está no PATH
1. Reinstale Python marcando "Add Python to PATH"
2. Ou adicione manualmente: `C:\Python311` ao PATH do Windows

### Erro: "node não é reconhecido"
**Solução**: Node não está no PATH
1. Reinstale Node.js
2. Reinicie o terminal/PowerShell

### Erro: "Script desabilitado" no PowerShell
**Solução**:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

### Porta 8001 ou 5173 já em uso
**Solução**: Encontre e mate o processo:
```cmd
netstat -ano | findstr :8001
taskkill /F /PID [número_do_processo]
```

### Chrome Debug não conecta
**Solução**:
1. Feche TODOS os Chromes abertos
2. Execute `iniciar_chrome_debug.bat` novamente
3. Use APENAS o Chrome que abrir (janela roxa)

---

## 📁 Estrutura do Projeto

```
fba-automation/
├── backend/              # Servidor Python/FastAPI
│   ├── venv/            # Virtual environment Python
│   ├── api/             # Rotas da API
│   └── main.py          # Arquivo principal
├── frontend/            # Interface React
│   ├── src/             # Código fonte
│   ├── node_modules/    # Dependências Node
│   └── package.json     # Configuração Node
├── instalar_windows.ps1 # Script de instalação
├── iniciar_tudo.bat     # Inicia tudo automaticamente
└── iniciar_chrome_debug.bat  # Inicia só o Chrome Debug
```

---

## 🔧 Scripts Disponíveis

### `instalar_windows.ps1`
Instala todas as dependências automaticamente

### `iniciar_tudo.bat`
Inicia Backend + Frontend + Chrome Debug de uma vez

### `iniciar_chrome_debug.bat`
Inicia apenas o Chrome Debug (porta 9222)

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique se tem permissões de Administrador
2. Verifique sua conexão com internet
3. Tente instalar manualmente (veja seção "Instalação Manual")
4. Verifique os logs de erro no terminal

---

## ✅ Checklist de Instalação

- [ ] Python 3.11 instalado (`python --version`)
- [ ] Node.js instalado (`node --version`)
- [ ] Google Chrome instalado
- [ ] Dependências Python instaladas
- [ ] Dependências Node.js instaladas
- [ ] Backend inicia sem erros (porta 8001)
- [ ] Frontend inicia sem erros (porta 5173)
- [ ] Chrome Debug conecta (porta 9222)

---

## 🎉 Pronto!

Agora você está pronto para usar o sistema de automação FBA!

**Próximos passos:**
1. Execute `iniciar_tudo.bat`
2. Acesse `http://localhost:5173`
3. Use o Chrome Debug para abrir produtos
4. Capture e exporte seus produtos
