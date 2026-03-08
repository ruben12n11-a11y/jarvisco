#!/bin/bash
echo "Instalando JarvisCO..."
cp jarvisco $PREFIX/bin/ 2>/dev/null || cp jarvisco /usr/local/bin/
chmod +x $PREFIX/bin/jarvisco 2>/dev/null || chmod +x /usr/local/bin/jarvisco
echo "✅ Instalación completada"
echo "Ejecuta: jarvisco"
