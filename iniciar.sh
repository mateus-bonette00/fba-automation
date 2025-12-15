#!/bin/bash

# Script para iniciar o sistema de automação FBA
# Instala dependências e roda o servidor

echo "=========================================="
echo "🚀 INICIANDO FBA AUTOMATION"
echo "=========================================="
echo ""

# Cor para mensagens
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="/home/mateus/Documentos/Qota Store/códigos/fba-automation"
cd "$PROJECT_DIR"

# 1. Verificar se requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: requirements.txt não encontrado!${NC}"
    exit 1
fi

# 2. Instalar dependências Python
echo -e "${YELLOW}📦 Instalando dependências do Python...${NC}"
pip3 install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependências Python instaladas!${NC}"
else
    echo -e "${RED}❌ Erro ao instalar dependências Python${NC}"
    echo "Tentando com --user..."
    pip3 install --user -r requirements.txt
fi

echo ""

# 3. Verificar se Playwright está instalado
echo -e "${YELLOW}🌐 Verificando Playwright...${NC}"
python3 -c "import playwright" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Instalando Playwright...${NC}"
    pip3 install playwright
fi

# Instalar navegadores do Playwright
echo -e "${YELLOW}📥 Instalando navegadores do Playwright...${NC}"
python3 -m playwright install chromium 2>&1 | grep -v "Downloading" | grep -v "chromium"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Playwright configurado!${NC}"
fi

echo ""

# 4. Verificar se o main.py existe
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}❌ Erro: backend/main.py não encontrado!${NC}"
    exit 1
fi

# 5. Mostrar informações
echo ""
echo "=========================================="
echo -e "${GREEN}✅ TUDO PRONTO!${NC}"
echo "=========================================="
echo ""
echo "📍 Servidor será iniciado em: http://localhost:8001"
echo "📖 Documentação da API: http://localhost:8001/docs"
echo ""
echo "🔍 Para capturar produtos de abas abertas:"
echo "   1. Abra o Chrome com: google-chrome --remote-debugging-port=9222"
echo "   2. Abra as páginas de produtos"
echo "   3. Use a API: http://localhost:8001/api/capture/capture-tabs"
echo ""
echo "📊 Para fazer scraping de um fornecedor:"
echo "   Use: http://localhost:8001/api/supplier/scrape"
echo ""
echo "⭐ Agora com 15 métodos de extração de UPC!"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}🚀 Iniciando servidor...${NC}"
echo ""

# 6. Rodar o servidor
cd backend
python3 main.py
