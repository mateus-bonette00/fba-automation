# FBA AUTOMATION - INSTALAÇÃO AUTOMÁTICA PARA WINDOWS

## 🚀 INSTALAÇÃO COMPLETA COM 1 ÚNICO COMANDO

Este projeto agora possui um **instalador totalmente automático** que configura TUDO em uma única execução!

---

## ⚡ MÉTODO RÁPIDO (RECOMENDADO)

### Passo 1: Baixar o Projeto
Se ainda não tem o projeto, clone ou baixe:
```bash
git clone [URL-DO-REPOSITORIO]
```

### Passo 2: Executar o Instalador Completo

1. **Clique com botão direito** no arquivo:
   ```
   INSTALAR_E_INICIAR_COMPLETO.bat
   ```

2. Selecione **"Executar como administrador"**

3. Clique **"Sim"** quando o Windows pedir permissão

4. **Aguarde** (10-15 minutos) - o script vai instalar TUDO automaticamente

5. Ao final, digite **S** para iniciar o projeto imediatamente

---

## 📦 O QUE SERÁ INSTALADO AUTOMATICAMENTE

O script `INSTALAR_E_INICIAR_COMPLETO.bat` instala:

### Software Base
- ✅ **Chocolatey** - Gerenciador de pacotes do Windows
- ✅ **Python 3.11** - Interpretador Python completo
- ✅ **Node.js 20 LTS** - Runtime JavaScript + npm
- ✅ **Google Chrome** - Navegador web
- ✅ **Git** - Sistema de controle de versão
- ✅ **Visual C++ Build Tools** - Compilador (necessário para alguns pacotes)

### Dependências Python (Backend)
- ✅ **FastAPI 0.109.0** - Framework web moderno
- ✅ **Uvicorn 0.27.0** - Servidor ASGI de alta performance
- ✅ **Playwright 1.40.0** - Automação de navegadores
- ✅ **Pandas 2.1.3** - Análise e manipulação de dados
- ✅ **Requests 2.31.0** - Cliente HTTP
- ✅ **BeautifulSoup4 4.12.2** - Parser HTML/XML
- ✅ **python-multipart 0.0.6** - Suporte para upload de arquivos
- ✅ **lxml 4.9.3** - Processamento XML/HTML rápido

### Dependências Node.js (Frontend)
- ✅ **React 18.2.0** - Biblioteca de interface
- ✅ **React DOM 18.2.0** - Renderização React
- ✅ **React Router 6.20.0** - Roteamento de páginas
- ✅ **Vite 5.0.0** - Build tool super rápida
- ✅ **@vitejs/plugin-react** - Plugin Vite para React

### Configurações Automáticas
- ✅ Virtual Environment Python (`backend/venv`)
- ✅ Navegadores Playwright (Chromium)
- ✅ Pastas necessárias (`logs`, `backend/data`)
- ✅ Variáveis de ambiente do sistema

---

## 🎯 COMO USAR APÓS A INSTALAÇÃO

### Iniciar o Projeto

Existem **3 formas** de iniciar o projeto após instalado:

#### Opção 1: Script Completo (Recomendado)
Duplo clique em:
```
INICIAR_TUDO.bat
```

Este script inicia automaticamente:
- Chrome Debug (porta 9222)
- Backend Python/FastAPI (porta 8001)
- Frontend React/Vite (porta 5173)

#### Opção 2: Manual (3 comandos)

**Terminal 1 - Chrome Debug:**
```batch
INICIAR_CHROME_DEBUG.bat
```

**Terminal 2 - Backend:**
```batch
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 3 - Frontend:**
```batch
cd frontend
npm run dev
```

#### Opção 3: Reinstalar e Iniciar
```batch
INSTALAR_E_INICIAR_COMPLETO.bat
```

---

## 🌐 ACESSANDO O SISTEMA

Após iniciar, acesse:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:5173 | Interface do usuário (React) |
| **Backend API** | http://localhost:8001 | API REST (FastAPI) |
| **Documentação API** | http://localhost:8001/docs | Swagger UI interativo |
| **Chrome Debug** | porta 9222 | Chrome com debug habilitado |

---

## 📋 WORKFLOW DE USO

1. **Execute** `INICIAR_TUDO.bat` (abre 3 janelas)

2. **Use o Chrome Debug** (janela roxa) para:
   - Abrir novas abas (Ctrl + T)
   - Acessar URLs de produtos da Amazon
   - Deixar as abas carregarem

3. **Acesse** http://localhost:5173/capture no seu navegador normal

4. **Clique** em "Capturar Abas"

5. **Veja** os produtos sendo extraídos automaticamente

---

## 🔧 REQUISITOS DO SISTEMA

### Requisitos Mínimos
- **Windows 10** ou superior (64-bit)
- **2 GB** de espaço livre em disco
- **4 GB** de RAM
- **Conexão** com internet (para instalação)
- **Permissões** de administrador

### Requisitos Recomendados
- **Windows 11** (64-bit)
- **5 GB** de espaço livre
- **8 GB** de RAM
- **Conexão** rápida com internet

---

## ❓ SOLUÇÃO DE PROBLEMAS

### Erro: "Execute como Administrador"
**Problema:** Script não tem permissões suficientes

**Solução:**
1. Clique com botão direito no arquivo `.bat`
2. Selecione "Executar como administrador"
3. Clique "Sim" na janela de permissões

---

### Erro: "Falha ao instalar Chocolatey"
**Problema:** PowerShell bloqueado ou sem internet

**Solução:**
1. Abra PowerShell como administrador
2. Execute:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```
3. Execute o instalador novamente

---

### Erro: "Python não encontrado"
**Problema:** Python não foi instalado ou não está no PATH

**Solução:**
1. Baixe Python manualmente: https://www.python.org/downloads/
2. Durante instalação, marque "Add Python to PATH"
3. Execute o instalador novamente

---

### Erro: "Node não encontrado"
**Problema:** Node.js não foi instalado ou não está no PATH

**Solução:**
1. Baixe Node.js manualmente: https://nodejs.org/
2. Instale normalmente
3. Execute o instalador novamente

---

### Erro: "Porta 9222 em uso"
**Problema:** Já existe um Chrome rodando na porta 9222

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
netstat -ano | find "8001"
taskkill /F /PID [numero_do_pid]
```

---

### Erro: "npm install falhou"
**Problema:** Falha ao instalar dependências Node.js

**Solução:**
```batch
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

---

### Erro: "ModuleNotFoundError: No module named 'fastapi'"
**Problema:** Dependências Python não instaladas no venv

**Solução:**
```batch
cd backend
venv\Scripts\activate
pip install -r ..\requirements.txt
```

---

## 📂 ESTRUTURA DO PROJETO

```
fba-automation/
│
├── backend/                          # Backend Python/FastAPI
│   ├── api/                          # Endpoints da API
│   │   ├── capture.py                # Captura de abas do Chrome
│   │   ├── products.py               # Gerenciamento de produtos
│   │   ├── sellers.py                # Gerenciamento de vendedores
│   │   └── supplier_scraper_v2.py    # Scraper de fornecedores
│   ├── data/                         # Dados da aplicação
│   ├── venv/                         # Virtual environment (criado automaticamente)
│   ├── main.py                       # Entry point do backend
│   └── requirements.txt              # Dependências Python
│
├── frontend/                         # Frontend React/Vite
│   ├── src/                          # Código-fonte React
│   │   ├── pages/                    # Páginas da aplicação
│   │   ├── components/               # Componentes reutilizáveis
│   │   └── App.jsx                   # Componente principal
│   ├── node_modules/                 # Dependências (criado automaticamente)
│   ├── package.json                  # Dependências Node.js
│   └── vite.config.js                # Configuração Vite
│
├── logs/                             # Logs do sistema (criado automaticamente)
│
├── INSTALAR_E_INICIAR_COMPLETO.bat  # ⭐ INSTALADOR PRINCIPAL (EXECUTE ESTE!)
├── INICIAR_TUDO.bat                  # Inicia todos os serviços
├── INICIAR_CHROME_DEBUG.bat          # Inicia apenas Chrome Debug
├── INSTALAR_WINDOWS.bat              # Instalador antigo (sem auto-start)
├── requirements.txt                  # Dependências Python raiz
│
└── LEIA-ME_WINDOWS.md               # Este arquivo
```

---

## 🎓 COMANDOS ÚTEIS

### Verificar Versões Instaladas
```batch
python --version
node --version
npm --version
git --version
choco --version
```

### Atualizar Dependências Python
```batch
cd backend
venv\Scripts\activate
pip install --upgrade -r ..\requirements.txt
```

### Atualizar Dependências Node.js
```batch
cd frontend
npm update
```

### Limpar Cache
```batch
cd backend
venv\Scripts\activate
pip cache purge

cd ..\frontend
npm cache clean --force
```

### Reinstalar Tudo do Zero
```batch
REM Deletar virtual environment
rmdir /s /q backend\venv

REM Deletar node_modules
rmdir /s /q frontend\node_modules

REM Executar instalador
INSTALAR_E_INICIAR_COMPLETO.bat
```

---

## 🆘 SUPORTE

### Logs do Sistema
Os logs ficam em:
- **Backend:** `logs/backend.log`
- **Frontend:** `logs/frontend.log`

### Verificar Serviços Rodando
```batch
REM Verificar portas abertas
netstat -ano | find "9222"   :: Chrome Debug
netstat -ano | find "8001"   :: Backend
netstat -ano | find "5173"   :: Frontend
```

### Parar Todos os Serviços
```batch
REM Parar Chrome Debug
taskkill /F /IM chrome.exe

REM Parar Backend (encontre o PID primeiro)
netstat -ano | find "8001"
taskkill /F /PID [numero_do_pid]

REM Parar Frontend (encontre o PID primeiro)
netstat -ano | find "5173"
taskkill /F /PID [numero_do_pid]
```

---

## 🔄 ATUALIZAÇÕES

Para atualizar o projeto com novas mudanças do Git:

```batch
REM 1. Parar todos os serviços

REM 2. Fazer pull das mudanças
git pull

REM 3. Atualizar dependências Python
cd backend
venv\Scripts\activate
pip install --upgrade -r ..\requirements.txt

REM 4. Atualizar dependências Node.js
cd ..\frontend
npm install

REM 5. Reiniciar
cd ..
INICIAR_TUDO.bat
```

---

## 📝 NOTAS IMPORTANTES

1. **Sempre use Chrome Debug** para abrir produtos
   - NÃO use seu Chrome normal
   - O Chrome Debug é identificado pela tela roxa

2. **Mantenha as 3 janelas abertas** enquanto usar o sistema
   - Chrome Debug
   - Backend (Python)
   - Frontend (React)

3. **Para parar o sistema**, feche as 3 janelas

4. **Backup dos dados**: A pasta `backend/data` contém seus dados

5. **Primeira execução** demora mais (download de dependências)

6. **Execuções seguintes** são muito mais rápidas

---

## 🎉 PRONTO PARA USAR!

Agora você tem um instalador completamente automático que configura TUDO com um único comando!

Basta executar:
```
INSTALAR_E_INICIAR_COMPLETO.bat (como administrador)
```

E em 10-15 minutos, seu sistema estará 100% funcional! 🚀

---

## 📧 CONTATO

Se tiver problemas, verifique:
1. Os logs em `logs/`
2. As soluções de problemas acima
3. Os requisitos do sistema
