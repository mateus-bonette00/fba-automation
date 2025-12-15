#!/bin/bash

# Script para iniciar Backend, Frontend e Chrome Debug simultaneamente
# Uso: ./iniciar_tudo.sh

echo "=========================================="
echo "🚀 INICIANDO FBA AUTOMATION COMPLETO"
echo "=========================================="
echo ""

# Cores para mensagens
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="/home/mateus/Documentos/Qota Store/códigos/fba-automation"
cd "$PROJECT_DIR"

# Arquivo de log
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Limpar logs antigos
> "$BACKEND_LOG"
> "$FRONTEND_LOG"

# Função para limpar processos ao sair
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Encerrando todos os processos...${NC}"

    # Matar processos filhos
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Backend encerrado${NC}"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Frontend encerrado${NC}"
    fi

    # Matar Chrome debug
    lsof -ti:9222 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✅ Chrome debug encerrado${NC}"

    echo ""
    echo "👋 Até logo!"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

# ==========================================
# 1. INICIAR CHROME DEBUG
# ==========================================
echo -e "${BLUE}1️⃣  INICIANDO CHROME DEBUG...${NC}"
echo ""

# Executar script de Chrome debug em background
./iniciar_chrome_debug.sh &
CHROME_SCRIPT_PID=$!

# Aguardar Chrome iniciar (4 segundos)
sleep 5

# Verificar se Chrome está rodando
if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chrome debug iniciado na porta 9222${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar Chrome debug${NC}"
    exit 1
fi

echo ""

# ==========================================
# 2. INICIAR BACKEND
# ==========================================
echo -e "${BLUE}2️⃣  INICIANDO BACKEND...${NC}"
echo ""

# Verificar se virtual environment existe
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}📦 Criando virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    cd ..
fi

# Ativar venv e instalar dependências
echo -e "${YELLOW}📦 Instalando dependências do backend...${NC}"
cd backend
source venv/bin/activate
pip install -q -r ../requirements.txt

# Verificar Playwright
python3 -c "import playwright" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}📥 Instalando Playwright...${NC}"
    pip install -q playwright
    python3 -m playwright install chromium
fi

# Iniciar backend em background
echo -e "${YELLOW}🚀 Iniciando servidor backend...${NC}"
python3 main.py > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
cd ..

# Aguardar backend iniciar
sleep 3

# Verificar se backend está rodando
if curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend iniciado em http://localhost:8001${NC}"
else
    echo -e "${YELLOW}⏳ Backend ainda está iniciando...${NC}"
fi

echo ""

# ==========================================
# 3. INICIAR FRONTEND
# ==========================================
echo -e "${BLUE}3️⃣  INICIANDO FRONTEND...${NC}"
echo ""

cd frontend

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependências do frontend...${NC}"
    npm install
fi

# Iniciar frontend em background
echo -e "${YELLOW}🚀 Iniciando servidor frontend...${NC}"
npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
cd ..

# Aguardar frontend iniciar
sleep 3

echo -e "${GREEN}✅ Frontend iniciado${NC}"
echo ""

# ==========================================
# 4. STATUS FINAL
# ==========================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ SISTEMA TOTALMENTE INICIADO!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📍 Serviços rodando:${NC}"
echo ""
echo "   🌐 Frontend:     http://localhost:5173"
echo "   🔧 Backend API:  http://localhost:8001"
echo "   📖 Docs API:     http://localhost:8001/docs"
echo "   🌍 Chrome Debug: http://localhost:9222"
echo ""
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo ""
echo "   1. Acesse http://localhost:5173"
echo "   2. Use o Chrome que foi aberto (porta 9222)"
echo "   3. Abra as abas dos produtos no Chrome debug"
echo "   4. Volte ao frontend para capturar"
echo ""
echo -e "${BLUE}📊 Logs:${NC}"
echo ""
echo "   Backend:  tail -f $BACKEND_LOG"
echo "   Frontend: tail -f $FRONTEND_LOG"
echo ""
echo -e "${YELLOW}⚠️  Pressione Ctrl+C para encerrar tudo${NC}"
echo ""
echo "=========================================="
echo ""

# Manter script rodando e mostrar logs
tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
