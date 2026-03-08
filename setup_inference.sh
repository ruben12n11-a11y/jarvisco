#!/bin/bash

# setup_inference.sh - Instalador de infraestructura para jarvisco
# Este script descarga, compila y configura llama.cpp y Ollama en Termux.

set -e

echo "===================================================="
echo "   🚀 jarvisco - Instalador de Infraestructura"
echo "===================================================="

# 1. Preparar dependencias de sistema
echo -e "\n📦 Instalando dependencias de compilación..."
pkg update -y
pkg install -y git cmake clang make python ninja

# 2. Configurar directorios
JARVISCO_DIR="$HOME/jarvisco"
MODELS_DIR="$JARVISCO_DIR/llama.cpp/models"
mkdir -p "$MODELS_DIR"

# 3. Descargar y Compilar llama.cpp
if [ ! -d "$JARVISCO_DIR/llama.cpp" ]; then
    echo -e "\n📥 Descargando llama.cpp..."
    cd "$JARVISCO_DIR"
    git clone https://github.com/ggerganov/llama.cpp.git
fi

echo -e "\n🛠️ Compilando llama.cpp (esto puede tardar)..."
cd "$JARVISCO_DIR/llama.cpp"
mkdir -p build
cd build
cmake .. -G Ninja
ninja llama-cli

# Crear enlace simbólico para jarvisco
mkdir -p "$HOME/.jarvisco/bin"
ln -sf "$JARVISCO_DIR/llama.cpp/build/bin/llama-cli" "$HOME/.jarvisco/bin/llama-cli"

# 4. Instalar Ollama (si no existe)
if ! command -v ollama &> /dev/null; then
    echo -e "\n📥 Instalando Ollama para Termux..."
    # Nota: En Termux, Ollama se instala vía pkg o script oficial
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "\n✅ Ollama ya está instalado."
fi

# 5. Configurar Modelfile
echo -e "\n📝 Configurando Modelfile en Ollama..."
cd "$JARVISCO_DIR"
if [ -f "Modelfile" ]; then
    # Verificar si el modelo GGUF existe antes de crear
    if [ -f "$MODELS_DIR/qwen2.5-7b-instruct-q4_k_m.gguf" ]; then
        ollama create jarvisco -f Modelfile
        echo "✅ Modelo 'jarvisco' creado en Ollama."
    else
        echo "⚠️  Aviso: No se encontró el archivo GGUF en $MODELS_DIR."
        echo "   Descárgalo para poder ejecutar 'ollama create jarvisco -f Modelfile' más tarde."
    fi
else
    echo "❌ Error: No se encontró el archivo Modelfile."
fi

echo -e "\n===================================================="
echo "   ✅ INFRAESTRUCTURA LISTA"
echo "===================================================="
echo "1. llama.cpp compilado en: $JARVISCO_DIR/llama.cpp/build/bin/llama-cli"
echo "2. Ollama configurado."
echo "3. Binarios vinculados a ~/.jarvisco/bin/"
echo "===================================================="
