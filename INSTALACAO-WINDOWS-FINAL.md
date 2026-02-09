# 🚀 INSTALAÇÃO WINDOWS - GUIA FINAL

## 📋 PRÉ-REQUISITOS

Antes de instalar, você precisa:

1. **Git instalado** - Para clonar o repositório
   - Baixe em: https://git-scm.com/download/win
   - Durante instalação, marque "Add Git to PATH"

2. **Clonar o repositório**
   ```bash
   git clone https://github.com/seu-usuario/fba-automation.git
   cd fba-automation
   ```

---

## ⚡ INSTALAÇÃO AUTOMÁTICA (RECOMENDADA)

### Passo 1: Clonar o Repositório

```bash
# Abra PowerShell ou CMD
cd C:\projetos  # ou qualquer pasta de sua preferência

# Clone o repositório
git clone https://github.com/seu-usuario/fba-automation.git

# Entre na pasta
cd fba-automation
```

### Passo 2: Executar Instalador

1. **Clique com botão direito** em:
   ```
   CLIQUE-AQUI-PARA-INSTALAR.bat
   ```

2. Selecione: **"Executar como administrador"**

3. Clique **"Sim"** quando o Windows pedir permissão

4. **Aguarde 10-15 minutos**

5. Ao final, digite **S** para iniciar o projeto

6. **Pronto!** Sistema 100% instalado! 🎉

---

## 📦 O QUE SERÁ INSTALADO

### Software Base (5 itens)
- ✅ **Chocolatey** - Gerenciador de pacotes Windows
- ✅ **Python 3.11** - Interpretador Python
- ✅ **Node.js 20 LTS** - Runtime JavaScript + npm
- ✅ **Google Chrome** - Navegador web
- ✅ **Visual C++ Build Tools** - Compilador C++

### Dependências Python (8 pacotes)
- ✅ **FastAPI 0.109.0** - Framework web moderno
- ✅ **Uvicorn 0.27.0** - Servidor ASGI
- ✅ **Playwright 1.40.0** - Automação de navegadores
- ✅ **Pandas 2.1.3** - Análise de dados
- ✅ **Requests 2.31.0** - Cliente HTTP
- ✅ **BeautifulSoup4 4.12.2** - Parser HTML/XML
- ✅ **python-multipart 0.0.6** - Upload de arquivos
- ✅ **lxml 4.9.3** - Processamento XML/HTML

### Dependências Node.js (5 pacotes)
- ✅ **React 18.2.0** - Biblioteca de interface
- ✅ **React DOM 18.2.0** - Renderização React
- ✅ **React Router 6.20.0** - Roteamento
- ✅ **Vite 5.0.0** - Build tool super rápida
- ✅ **@vitejs/plugin-react** - Plugin Vite

### Configurações (3 itens)
- ✅ **Virtual Environment** Python (backend/venv)
- ✅ **Navegadores Playwright** (Chromium)
- ✅ **Pastas do projeto** (logs, backend/data)

---

## 🎯 COMO USAR APÓS INSTALAÇÃO

### Iniciar o Sistema

```batch
# Duplo clique em:
INICIAR_TUDO.bat
```

Isso vai abrir **3 janelas**:
1. Chrome Debug (porta 9222) - janela roxa
2. Backend Python/FastAPI (porta 8001)
3. Frontend React/Vite (porta 5173)

### Acessar o Sistema

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:5173 | Interface React |
| **Backend API** | http://localhost:8001 | API FastAPI |
| **Docs API** | http://localhost:8001/docs | Swagger UI |
| **Chrome Debug** | porta 9222 | Chrome com debug |

### Workflow Básico

1. **Execute:** `INICIAR_TUDO.bat`

2. **Use o Chrome Debug** (janela roxa):
   - Abra novas abas (Ctrl + T)
   - Acesse URLs de produtos da Amazon
   - Deixe as páginas carregarem

3. **Acesse:** http://localhost:5173/capture

4. **Clique:** "Capturar Abas"

5. **Veja** os produtos sendo extraídos!

---

## 📁 ESTRUTURA DO PROJETO

```
fba-automation/
│
├── CLIQUE-AQUI-PARA-INSTALAR.bat      ⭐ Execute este para instalar
├── SCRIPT-CORRETO.bat                  🔧 Instalador principal (chamado pelo anterior)
├── INICIAR_TUDO.bat                    ▶️ Inicia todos os serviços
├── INICIAR_CHROME_DEBUG.bat            🌐 Inicia Chrome Debug
│
├── backend/
│   ├── venv/                           🐍 (criado automaticamente)
│   ├── api/                            📡 Endpoints da API
│   ├── data/                           💾 Dados da aplicação
│   ├── main.py                         🚀 Entry point
│   └── requirements.txt                📦 Dependências Python
│
├── frontend/
│   ├── node_modules/                   📦 (criado automaticamente)
│   ├── src/                            ⚛️ Código React
│   ├── package.json                    📋 Dependências Node.js
│   └── vite.config.js                  ⚙️ Configuração Vite
│
└── logs/                               📊 (criado automaticamente)
```

---

## 🔧 COMANDOS ÚTEIS

### Atualizar o Projeto

```bash
# Baixar últimas mudanças do GitHub
git pull

# Atualizar dependências Python
cd backend
venv\Scripts\activate
pip install --upgrade -r ..\requirements.txt

# Atualizar dependências Node.js
cd ..\frontend
npm update
```

### Verificar Versões

```batch
python --version
node --version
npm --version
git --version
choco --version
```

### Parar Todos os Serviços

```batch
# Parar Chrome Debug
taskkill /F /IM chrome.exe

# Parar Python (Backend)
taskkill /F /IM python.exe

# Parar Node (Frontend)
taskkill /F /IM node.exe
```

### Reinstalar do Zero

```batch
# Deletar virtual environment
rmdir /s /q backend\venv

# Deletar node_modules
rmdir /s /q frontend\node_modules

# Executar instalador novamente
CLIQUE-AQUI-PARA-INSTALAR.bat (como administrador)
```

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro: "Execute como Administrador"

**Problema:** Script não tem permissões

**Solução:**
1. Clique com botão direito no arquivo `.bat`
2. Selecione "Executar como administrador"
3. Clique "Sim" na janela de permissões

---

### Erro: "Python não encontrado"

**Problema:** Python não instalado ou não está no PATH

**Solução:**
```batch
# Verificar se Python está instalado
python --version

# Se não aparecer, reinstale:
choco install python311 -y --force

# Ou baixe manualmente:
# https://www.python.org/downloads/
```

---

### Erro: "Node não encontrado"

**Problema:** Node.js não instalado ou não está no PATH

**Solução:**
```batch
# Verificar se Node está instalado
node --version

# Se não aparecer, reinstale:
choco install nodejs-lts -y --force

# Ou baixe manualmente:
# https://nodejs.org/
```

---

### Erro: "Porta 9222 em uso"

**Problema:** Chrome Debug já está rodando

**Solução:**
```batch
taskkill /F /IM chrome.exe
timeout /t 2
INICIAR_CHROME_DEBUG.bat
```

---

### Erro: "Porta 8001 em uso"

**Problema:** Backend já está rodando

**Solução:**
```batch
# Descobrir PID do processo
netstat -ano | find "8001"

# Matar processo (substitua XXXX pelo PID)
taskkill /F /PID XXXX
```

---

### Erro: "npm install falhou"

**Problema:** Falha ao instalar dependências Node.js

**Solução:**
```batch
cd frontend

# Limpar cache
npm cache clean --force

# Deletar node_modules
rmdir /s /q node_modules
del package-lock.json

# Reinstalar
npm install
```

---

### Erro: "ModuleNotFoundError: No module named 'fastapi'"

**Problema:** Dependências Python não instaladas

**Solução:**
```batch
cd backend

# Ativar virtual environment
venv\Scripts\activate

# Reinstalar dependências
pip install -r ..\requirements.txt

# Verificar instalação
pip list | find "fastapi"
```

---

## 💡 DICAS IMPORTANTES

### ✅ Sempre Faça

1. **Use o Chrome Debug** (janela roxa) para abrir produtos
2. **Mantenha as 3 janelas abertas** enquanto usar o sistema
3. **Execute como Administrador** os scripts .bat
4. **Faça backup** da pasta `backend/data` (contém seus dados)
5. **Atualize** com `git pull` antes de usar

### ❌ Nunca Faça

1. **NÃO use seu Chrome normal** - não funcionará
2. **NÃO feche** as janelas do Chrome Debug, Backend e Frontend
3. **NÃO delete** a pasta `.git` (histórico do projeto)
4. **NÃO delete** `backend/venv` sem motivo
5. **NÃO execute** múltiplas vezes `INICIAR_TUDO.bat` simultaneamente

---

## 📊 REQUISITOS DO SISTEMA

### Mínimo
- **Windows:** 10 (64-bit)
- **Espaço:** 2 GB livres
- **RAM:** 4 GB
- **Internet:** Necessária para instalação
- **Admin:** Permissões de administrador

### Recomendado
- **Windows:** 11 (64-bit)
- **Espaço:** 5 GB livres
- **RAM:** 8 GB
- **Internet:** Conexão rápida
- **SSD:** Recomendado para melhor performance

---

## 🔄 WORKFLOW COMPLETO

### Primeira Vez (Com Git)

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/fba-automation.git
cd fba-automation

# 2. Executar instalador (como admin)
# Clique direito em: CLIQUE-AQUI-PARA-INSTALAR.bat
# Selecione: "Executar como administrador"

# 3. Aguardar instalação (10-15 min)

# 4. Iniciar sistema
# Duplo clique em: INICIAR_TUDO.bat

# 5. Acessar
# http://localhost:5173
```

### Próximas Vezes

```bash
# 1. Entrar na pasta
cd C:\projetos\fba-automation

# 2. Atualizar (opcional)
git pull

# 3. Iniciar
# Duplo clique em: INICIAR_TUDO.bat
```

---

## 📚 ARQUIVOS DO PROJETO

| Arquivo | Descrição |
|---------|-----------|
| `CLIQUE-AQUI-PARA-INSTALAR.bat` | ⭐ Instalador principal - USE ESTE! |
| `SCRIPT-CORRETO.bat` | Instalador completo (chamado pelo anterior) |
| `INICIAR_TUDO.bat` | Inicia todos os serviços |
| `INICIAR_CHROME_DEBUG.bat` | Inicia apenas Chrome Debug |
| `requirements.txt` | Dependências Python |
| `frontend/package.json` | Dependências Node.js |
| `LEIA-ISSO-PRIMEIRO.txt` | Guia rápido em texto |
| `GUIA-RAPIDO-WINDOWS.html` | Guia visual (abrir no navegador) |
| `INDEX.html` | Índice de todos os arquivos |

---

## 🎉 PRONTO PARA USAR!

Agora você tem um **instalador completamente automático** que:

✅ Instala **TUDO** (exceto Git, que deve estar instalado)
✅ Configura **TODO** o ambiente
✅ Executa **TUDO** com 1 clique
✅ Funciona em **QUALQUER** Windows 10/11

**Para instalar:**
```
1. Clone: git clone https://github.com/seu-usuario/fba-automation.git
2. Execute: CLIQUE-AQUI-PARA-INSTALAR.bat (como administrador)
3. Aguarde: 10-15 minutos
4. Pronto: Sistema 100% instalado! 🚀
```

---

## 📞 SUPORTE

### Logs
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`

### Verificar Serviços
```batch
netstat -ano | find "9222"   :: Chrome Debug
netstat -ano | find "8001"   :: Backend
netstat -ano | find "5173"   :: Frontend
```

### Status do Git
```bash
git status
git log --oneline -5
```

---

**Boa sorte e bom trabalho!** 🎊
