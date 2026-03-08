#!/bin/bash
# install_jarvisco.sh - Instalador para jarvisco en Termux

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Instalador de jarvisco - Copiloto Offline${NC}"

# 1. Directorios
JARVISCO_HOME="$HOME/.jarvisco"
mkdir -p "$JARVISCO_HOME"/{config,models,sessions,bin}

# 2. Detectar Modelos
echo -e "${YELLOW}Buscando modelos...${NC}"
MODEL_PATH="$HOME/jarvisco/llama.cpp/models/qwen2.5-7b-instruct-q4_k_m.gguf"

if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓ Modelo GGUF detectado en llama.cpp/models${NC}"
    ln -sf "$MODEL_PATH" "$JARVISCO_HOME/models/qwen2.5-7b-instruct-q4_k_m.gguf"
fi

if ollama list | grep -q "qwen3-coder:480b-cloud"; then
    echo -e "${GREEN}✓ Modelo detectado en Ollama${NC}"
fi

# 3. Copiar archivos
INSTALL_DIR="$PREFIX/lib/python3.11/site-packages/jarvisco"
mkdir -p "$INSTALL_DIR"
cp *.py "$INSTALL_DIR/"
cp jarvisco.gbnf "$JARVISCO_HOME/config/"

# 4. Crear ejecutable
cat > "$PREFIX/bin/jarvisco" << 'EOF'
#!/bin/bash
python3 -c "from jarvisco.interactive_chat import main; main()" "$@"
EOF
chmod +x "$PREFIX/bin/jarvisco"

echo -e "${GREEN}Instalación de jarvisco completada.${NC}"
