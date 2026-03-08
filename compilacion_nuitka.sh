#!/bin/bash
"""
compilacion_nuitka.sh - Script de Compilación con Nuitka

Propósito: Compilar jarvisco a binario único con Nuitka
Ventajas:
- Protección del código fuente
- Mejor rendimiento
- Distribución más fácil

Requisitos:
- Nuitka
- Clang (compilador C)
- Python 3.8+

Autor: Sergio Alberto Sanchez Echeverria
"""

set -e  # Salir si hay error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "============================================================"
echo "COMPILACIÓN DE JARVISCO A BINARIO CON NUITKA"
echo "============================================================"
echo -e "${NC}"

# Variables
PROJECT_DIR="$(pwd)"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$PROJECT_DIR/build"

echo ""
echo -e "${YELLOW}[1/5]${NC} Verificando dependencias..."
echo "============================================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}"

# Verificar Nuitka
if ! python3 -m pip show nuitka &> /dev/null; then
    echo -e "${YELLOW}⚠️  Nuitka no instalado, instalando...${NC}"
    python3 -m pip install nuitka
fi
echo -e "${GREEN}✅ Nuitka instalado${NC}"

# Verificar Clang (compilador)
if ! command -v clang &> /dev/null; then
    echo -e "${YELLOW}⚠️  Clang no encontrado${NC}"
    echo "En Termux: pkg install clang"
    echo "En Linux: apt-get install clang"
    exit 1
fi
echo -e "${GREEN}✅ Clang: $(clang --version | head -1)${NC}"

echo ""
echo -e "${YELLOW}[2/5]${NC} Limpiando directorios anteriores..."
echo "============================================================"

# Limpiar compilaciones anteriores
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
rm -rf "$PROJECT_DIR/__pycache__"
rm -rf "$PROJECT_DIR/.nuitka"
find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Directorios limpios${NC}"

echo ""
echo -e "${YELLOW}[3/5]${NC} Compilando con Nuitka (esto puede tardar varios minutos)..."
echo "============================================================"

# Compilar con Nuitka
# --standalone: Incluye todas las dependencias
# --onefile: Genera un único archivo ejecutable
# --follow-imports: Incluye todos los imports
# --remove-output: Limpia archivos temporales

python3 -m nuitka \
    --standalone \
    --onefile \
    --output-dir="$DIST_DIR" \
    --follow-imports \
    --include-data-files="jarvisco.gbnf=jarvisco.gbnf" \
    --remove-output \
    --assume-yes-for-downloads \
    --show-progress \
    --show-memory \
    interactive_chat.py

echo -e "${GREEN}✅ Compilación completada${NC}"

echo ""
echo -e "${YELLOW}[4/5]${NC} Verificando binario..."
echo "============================================================"

# Buscar binario generado
BINARY_PATH=""
if [ -f "$DIST_DIR/interactive_chat.bin" ]; then
    BINARY_PATH="$DIST_DIR/interactive_chat.bin"
elif [ -f "$DIST_DIR/interactive_chat" ]; then
    BINARY_PATH="$DIST_DIR/interactive_chat"
elif [ -f "$DIST_DIR/interactive_chat.exe" ]; then
    BINARY_PATH="$DIST_DIR/interactive_chat.exe"
else
    echo -e "${RED}❌ Binario no encontrado${NC}"
    exit 1
fi

# Renombrar a jarvisco
FINAL_BINARY="$DIST_DIR/jarvisco"
mv "$BINARY_PATH" "$FINAL_BINARY"
chmod +x "$FINAL_BINARY"

# Verificar tamaño
BINARY_SIZE=$(du -h "$FINAL_BINARY" | cut -f1)
echo -e "${GREEN}✅ Binario generado: $FINAL_BINARY${NC}"
echo -e "${GREEN}   Tamaño: $BINARY_SIZE${NC}"

echo ""
echo -e "${YELLOW}[5/5]${NC} Creando paquete de distribución..."
echo "============================================================"

# Crear directorio de distribución
PACKAGE_DIR="$DIST_DIR/jarvisco-package"
mkdir -p "$PACKAGE_DIR"

# Copiar binario
cp "$FINAL_BINARY" "$PACKAGE_DIR/"

# Copiar archivos necesarios
cp jarvisco.gbnf "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/" 2>/dev/null || echo "# JarvisCO" > "$PACKAGE_DIR/README.md"

# Crear script de instalación simple
cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash
echo "Instalando JarvisCO..."
cp jarvisco $PREFIX/bin/ 2>/dev/null || cp jarvisco /usr/local/bin/
chmod +x $PREFIX/bin/jarvisco 2>/dev/null || chmod +x /usr/local/bin/jarvisco
echo "✅ Instalación completada"
echo "Ejecuta: jarvisco"
EOF
chmod +x "$PACKAGE_DIR/install.sh"

echo -e "${GREEN}✅ Paquete creado en: $PACKAGE_DIR${NC}"

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ COMPILACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "📦 Archivos generados:"
echo "  • Binario:  $FINAL_BINARY"
echo "  • Paquete:  $PACKAGE_DIR"
echo ""
echo "🚀 Para instalar:"
echo "  $ cd $PACKAGE_DIR"
echo "  $ bash install.sh"
echo ""
echo "🚀 O ejecutar directamente:"
echo "  $ $FINAL_BINARY"
echo ""
echo -e "${YELLOW}Nota:${NC} El binario NO incluye el modelo GGUF (es muy grande)"
echo "      Debes tener el modelo en ~/.jarvisco/models/"
echo ""
