# FBA Automation - Instalação Windows

## 🚀 Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/fba-automation.git
cd fba-automation
```

### 2. Instalar Tudo Automaticamente

**Duplo clique em:**
```
INSTALAR-WINDOWS.bat
```

O script vai:
- Pedir permissões de administrador automaticamente
- Instalar Python, Node.js, Chrome e todas as dependências
- Configurar o ambiente completo
- Demorar 10-15 minutos

### 3. Iniciar o Sistema

**Duplo clique em:**
```
INICIAR_TUDO.bat
```

Abre 3 janelas:
- Chrome Debug (porta 9222)
- Backend (porta 8001)
- Frontend (porta 5173)

### 4. Acessar

http://localhost:5173

---

## 📦 O Que Será Instalado

- Chocolatey (gerenciador de pacotes)
- Python 3.11
- Node.js 20 LTS
- Google Chrome
- Visual C++ Build Tools
- FastAPI, Uvicorn, Playwright, Pandas
- React, Vite, React Router

---

## 🔧 Comandos Úteis

### Atualizar do GitHub
```bash
git pull
```

### Parar Tudo
```bash
taskkill /F /IM chrome.exe
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

### Reinstalar
```bash
rmdir /s /q backend\venv
rmdir /s /q frontend\node_modules
INSTALAR-WINDOWS.bat (duplo clique)
```

---

## 📁 Arquivos Principais

- `INSTALAR-WINDOWS.bat` - Instalador automático
- `INICIAR_TUDO.bat` - Inicia todos os serviços
- `INICIAR_CHROME_DEBUG.bat` - Inicia Chrome Debug
- `requirements.txt` - Dependências Python
- `frontend/package.json` - Dependências Node.js

---

## 🐛 Problemas?

### Script fecha sozinho
- Execute com duplo clique (não precisa botão direito)
- O script pede admin automaticamente

### Porta em uso
```bash
netstat -ano | find "8001"
taskkill /F /PID [numero]
```

---

**Pronto para usar!** 🎉
