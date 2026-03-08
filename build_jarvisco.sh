#!/bin/bash
"""
build_jarvisco.sh - Script de Compilación Simplificado

Propósito: Compilar jarvisco rápidamente para Termux
Este script es más simple que compilacion_nuitka.sh y está
optimizado para desarrollo rápido.

Autor: Sergio Alberto Sanchez Echeverria
"""

echo "🚀 Iniciando compilación de JarvisCO en Termux..."

# Limpiar restos
rm -rf dist build

# Compilar a binario standalone
# Esto protege tu código y empaqueta las librerías
python3 -m nuitka \
    --standalone \
    --output-dir=dist \
    --include-data-files=jarvisco.gbnf=jarvisco.gbnf \
    --show-progress \
    interactive_chat.py

# Verificar si la compilación fue exitosa
if [ $? -ne 0 ]; then
    echo "❌ Error en compilación"
    exit 1
fi

# Instalar en el sistema de Termux
echo "📦 Instalando binario..."
mkdir -p ~/.jarvisco/app

# Copiar archivos compilados
if [ -d "dist/interactive_chat.dist" ]; then
    cp -r dist/interactive_chat.dist/* ~/.jarvisco/app/
    ln -sf ~/.jarvisco/app/interactive_chat $PREFIX/bin/jarvisco
elif [ -f "dist/interactive_chat.bin" ]; then
    cp dist/interactive_chat.bin ~/.jarvisco/app/jarvisco
    ln -sf ~/.jarvisco/app/jarvisco $PREFIX/bin/jarvisco
elif [ -f "dist/interactive_chat" ]; then
    cp dist/interactive_chat ~/.jarvisco/app/jarvisco
    ln -sf ~/.jarvisco/app/jarvisco $PREFIX/bin/jarvisco
else
    echo "❌ No se encontró el binario compilado"
    exit 1
fi

chmod +x $PREFIX/bin/jarvisco

echo "✅ ¡LISTO! Ahora puedes usar el comando: jarvisco"
