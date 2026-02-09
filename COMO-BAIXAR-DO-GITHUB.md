# 📥 COMO BAIXAR E INSTALAR DO GITHUB

Este guia mostra como baixar o projeto FBA Automation do GitHub e instalar TUDO automaticamente no Windows.

---

## 🚀 MÉTODO 1: SCRIPT AUTOMÁTICO (RECOMENDADO)

Este método **FAZ TUDO AUTOMATICAMENTE**: baixa o Git, clona o repositório e instala todas as dependências!

### Passo 1: Baixar o Script Instalador

1. Acesse o repositório no GitHub
2. Clique em **Code** → **Download ZIP**
3. Extraia apenas o arquivo: `BAIXAR-E-INSTALAR-DO-GITHUB.bat`
4. Salve em algum lugar do seu computador (ex: `C:\Downloads`)

### Passo 2: Executar o Instalador

1. **Clique com botão direito** em:
   ```
   BAIXAR-E-INSTALAR-DO-GITHUB.bat
   ```

2. Selecione **"Executar como administrador"**

3. Clique **"Sim"** quando o Windows pedir permissão

4. O script vai perguntar:
   ```
   Digite a URL do repositório GitHub:
   ```

   Cole a URL do seu repositório, exemplo:
   ```
   https://github.com/seu-usuario/fba-automation.git
   ```

5. O script vai perguntar:
   ```
   Onde deseja clonar o projeto?
   ```

   Digite o caminho desejado ou deixe vazio para usar `C:\fba-automation`:
   ```
   C:\projetos\fba-automation
   ```
   (ou deixe vazio para usar C:\fba-automation)

6. **Aguarde 15-20 minutos** - O script vai:
   - ✅ Instalar Git (se necessário)
   - ✅ Clonar o repositório do GitHub
   - ✅ Instalar Python, Node.js, Chrome, etc.
   - ✅ Instalar todas as dependências
   - ✅ Configurar o ambiente completo

7. Ao final, digite **S** para iniciar o projeto

8. **Pronto!** Sistema 100% instalado e funcionando! 🎉

---

## 📦 MÉTODO 2: MANUAL COM GIT

Se você já tem o Git instalado, pode clonar manualmente:

### Passo 1: Instalar Git (se não tiver)

Baixe e instale: https://git-scm.com/download/win

### Passo 2: Clonar o Repositório

Abra o PowerShell ou CMD e execute:

```bash
# Navegar para a pasta desejada
cd C:\projetos

# Clonar o repositório
git clone https://github.com/seu-usuario/fba-automation.git

# Entrar na pasta
cd fba-automation
```

### Passo 3: Executar o Instalador

```batch
# Clique com botão direito e execute como administrador:
CLIQUE-AQUI-PARA-INSTALAR.bat
```

Aguarde 10-15 minutos e pronto!

---

## 💻 MÉTODO 3: DOWNLOAD ZIP (SEM GIT)

Se você não quer usar Git:

### Passo 1: Baixar o Projeto

1. Acesse: https://github.com/seu-usuario/fba-automation
2. Clique em **Code** (botão verde)
3. Clique em **Download ZIP**
4. Salve o arquivo (ex: `fba-automation-main.zip`)

### Passo 2: Extrair o ZIP

1. Clique com botão direito no arquivo ZIP
2. Selecione **Extrair tudo...**
3. Escolha a pasta de destino (ex: `C:\projetos`)
4. Clique em **Extrair**

### Passo 3: Executar o Instalador

1. Entre na pasta extraída
2. **Clique com botão direito** em:
   ```
   CLIQUE-AQUI-PARA-INSTALAR.bat
   ```
3. Selecione **"Executar como administrador"**
4. Aguarde 10-15 minutos
5. Pronto!

---

## 🔄 O QUE SERÁ INSTALADO

### Software Base
- ✅ **Git** - Sistema de controle de versão
- ✅ **Chocolatey** - Gerenciador de pacotes Windows
- ✅ **Python 3.11** - Interpretador Python
- ✅ **Node.js 20 LTS** - Runtime JavaScript
- ✅ **Google Chrome** - Navegador
- ✅ **Visual C++ Build Tools** - Compilador

### Dependências Python (Backend)
- ✅ FastAPI 0.109.0
- ✅ Uvicorn 0.27.0
- ✅ Playwright 1.40.0
- ✅ Pandas 2.1.3
- ✅ Requests 2.31.0
- ✅ BeautifulSoup4 4.12.2
- ✅ python-multipart 0.0.6
- ✅ lxml 4.9.3

### Dependências Node.js (Frontend)
- ✅ React 18.2.0
- ✅ React DOM 18.2.0
- ✅ React Router 6.20.0
- ✅ Vite 5.0.0
- ✅ @vitejs/plugin-react

---

## 🌐 ACESSANDO O SISTEMA

Após a instalação, acesse:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:5173 | Interface React |
| **Backend API** | http://localhost:8001 | API FastAPI |
| **Docs API** | http://localhost:8001/docs | Swagger UI |
| **Chrome Debug** | porta 9222 | Chrome com debug |

---

## 📋 COMANDOS GIT ÚTEIS

### Atualizar o Projeto

```bash
# Entrar na pasta do projeto
cd C:\projetos\fba-automation

# Baixar últimas mudanças
git pull
```

### Verificar Status

```bash
# Ver arquivos modificados
git status

# Ver diferenças
git diff
```

### Descartar Mudanças Locais

```bash
# Descartar todas as mudanças
git reset --hard

# Baixar última versão
git pull
```

### Clonar em Pasta Específica

```bash
# Clonar para uma pasta específica
git clone https://github.com/seu-usuario/fba-automation.git C:\MeusProjetos\FBA
```

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### Erro: "Git não encontrado"

**Problema:** Git não está instalado ou não está no PATH

**Solução:**
1. Execute: `BAIXAR-E-INSTALAR-DO-GITHUB.bat` (instala Git automaticamente)

OU

2. Baixe Git manualmente: https://git-scm.com/download/win
3. Durante instalação, marque "Add Git to PATH"

---

### Erro: "Repository not found" ou "Access denied"

**Problema:** URL incorreta ou repositório privado sem acesso

**Solução:**
1. Verifique se a URL está correta
2. Se o repositório for privado, você precisa:
   - Fazer login no GitHub via Git
   - Ou usar token de acesso pessoal
   - Ou usar chave SSH

**Como fazer login:**
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@example.com"

# Na primeira vez, o Git vai pedir suas credenciais
git clone https://github.com/seu-usuario/fba-automation.git
```

---

### Erro: "fatal: destination path already exists"

**Problema:** Pasta já existe

**Solução:**
```bash
# Opção 1: Clonar em pasta diferente
git clone https://github.com/seu-usuario/fba-automation.git fba-automation-novo

# Opção 2: Deletar pasta existente
rmdir /s /q fba-automation
git clone https://github.com/seu-usuario/fba-automation.git

# Opção 3: Usar a pasta existente
cd fba-automation
git pull
```

---

### Erro: "Permission denied" ao clonar

**Problema:** Sem permissões para criar pasta

**Solução:**
1. Execute o CMD ou PowerShell como Administrador
2. Ou clone em uma pasta onde você tem permissões (ex: `C:\Users\SeuNome\Documents`)

---

### Erro ao instalar dependências após clonar

**Problema:** Arquivos não encontrados ou corrompidos

**Solução:**
```bash
# Entrar na pasta
cd fba-automation

# Verificar se tudo foi baixado corretamente
git status

# Baixar arquivos faltantes
git pull

# Executar instalador
CLIQUE-AQUI-PARA-INSTALAR.bat
```

---

## 📁 ESTRUTURA APÓS CLONAR

```
C:\projetos\fba-automation\     (ou onde você escolheu)
│
├── BAIXAR-E-INSTALAR-DO-GITHUB.bat    ⭐ Script para clonar e instalar
├── CLIQUE-AQUI-PARA-INSTALAR.bat      💿 Instalador (após clonar)
├── INICIAR_TUDO.bat                    ▶️ Iniciar projeto
│
├── backend/
│   ├── api/
│   ├── main.py
│   └── requirements.txt                📦 Dependências Python
│
├── frontend/
│   ├── src/
│   ├── package.json                    📦 Dependências Node.js
│   └── vite.config.js
│
└── README.md
```

---

## 🎯 WORKFLOW COMPLETO (DO ZERO)

### Primeira Vez (Com Internet)

1. **Baixar o script instalador:**
   - Pegue apenas: `BAIXAR-E-INSTALAR-DO-GITHUB.bat`
   - OU baixe tudo e extraia

2. **Executar como administrador:**
   ```
   BAIXAR-E-INSTALAR-DO-GITHUB.bat (botão direito → executar como admin)
   ```

3. **Informar URL do GitHub:**
   ```
   https://github.com/seu-usuario/fba-automation.git
   ```

4. **Aguardar instalação:**
   - 15-20 minutos
   - Tudo será instalado automaticamente

5. **Iniciar o projeto:**
   - Digite "S" ao final
   - OU execute: `INICIAR_TUDO.bat`

### Próximas Vezes (Já Instalado)

1. **Ir para a pasta do projeto:**
   ```bash
   cd C:\projetos\fba-automation
   ```

2. **Atualizar código (opcional):**
   ```bash
   git pull
   ```

3. **Iniciar:**
   ```
   INICIAR_TUDO.bat (duplo clique)
   ```

---

## 💡 DICAS IMPORTANTES

### ✅ Boas Práticas

1. **Sempre clone em pasta com permissões:**
   - ✅ `C:\Users\SeuNome\Documents\projetos`
   - ✅ `C:\projetos` (se tiver permissões)
   - ❌ `C:\Program Files` (evite, precisa admin)

2. **Use caminhos sem espaços (se possível):**
   - ✅ `C:\projetos\fba-automation`
   - ⚠️ `C:\Meus Projetos\fba automation` (funciona, mas pode causar problemas)

3. **Mantenha Git atualizado:**
   ```bash
   git --version
   choco upgrade git
   ```

4. **Configure Git antes de clonar repositórios privados:**
   ```bash
   git config --global user.name "Seu Nome"
   git config --global user.email "seu-email@example.com"
   ```

### ⚠️ Atenção

1. **NÃO delete a pasta `.git`** - contém histórico do projeto

2. **Para atualizar o projeto:**
   - Use: `git pull` (preserva suas mudanças)
   - NÃO delete e clone novamente (perde suas alterações)

3. **Backup de dados:**
   - A pasta `backend/data` contém seus dados
   - Faça backup antes de `git pull`

---

## 📞 SUPORTE

### Verificar se Git foi instalado

```bash
git --version
```

Deve mostrar algo como: `git version 2.43.0.windows.1`

### Verificar se o projeto foi clonado

```bash
cd C:\projetos\fba-automation
git status
```

Deve mostrar: `On branch master` (ou main)

### Logs de Instalação

Se algo der errado, verifique os logs em:
- `logs/backend.log`
- `logs/frontend.log`

---

## 🎉 PRONTO PARA COMEÇAR!

Agora você tem **3 formas** de baixar e instalar o projeto:

1. ⭐ **Script Automático** - `BAIXAR-E-INSTALAR-DO-GITHUB.bat` (RECOMENDADO)
2. 🔧 **Manual com Git** - `git clone` + `CLIQUE-AQUI-PARA-INSTALAR.bat`
3. 📦 **Download ZIP** - Baixar ZIP + `CLIQUE-AQUI-PARA-INSTALAR.bat`

**Escolha o método que preferir e bom trabalho!** 🚀

---

## 📚 Próximos Passos

Após instalar, leia:
- `LEIA-ISSO-PRIMEIRO.txt` - Guia básico de uso
- `GUIA-RAPIDO-WINDOWS.html` - Guia visual completo
- `LEIA-ME_WINDOWS.md` - Documentação detalhada
