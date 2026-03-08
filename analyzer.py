#!/usr/bin/env python3
"""
analyzer.py - Analizador de Código Python usando AST

Propósito: Analizar código fuente Python para extraer información estructural
Utiliza: Abstract Syntax Tree (AST) de Python

Extrae:
- Imports y dependencias
- Funciones definidas
- Clases definidas
- Complejidad ciclomática aproximada

Autor: Sergio Alberto Sanchez Echeverria
"""

import ast
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Analizador de código Python usando AST

    Extrae información estructural del código sin ejecutarlo:
    - Imports
    - Funciones
    - Clases
    - Complejidad ciclomática
    """

    def __init__(self, source_code: str):
        """
        Inicializar analizador con código fuente

        Args:
            source_code: Código Python a analizar
        """
        self.source_code = source_code
        self.imports = []
        self.functions = []
        self.classes = []
        self.complexity = 0
        self.syntax_error = None
        self.tree = None

    def analyze(self) -> None:
        """
        Analizar el código fuente

        Parsea el código y extrae toda la información estructural
        """
        try:
            # Parsear código a AST
            self.tree = ast.parse(self.source_code)
            logger.debug("Código parseado exitosamente")

        except SyntaxError as e:
            # Capturar error de sintaxis
            self.syntax_error = f"{e.__class__.__name__}: {e.msg} (línea {e.lineno})"
            logger.error(f"Error de sintaxis: {self.syntax_error}")
            return

        except Exception as e:
            # Capturar otros errores
            self.syntax_error = f"{e.__class__.__name__}: {str(e)}"
            logger.error(f"Error al parsear: {self.syntax_error}")
            return

        # Recorrer el árbol AST
        for node in ast.walk(self.tree):

            # Detectar imports simples (import x)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(alias.name)

            # Detectar imports from (from x import y)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports.append(node.module)

            # Detectar funciones
            elif isinstance(node, ast.FunctionDef):
                self.functions.append(node.name)
                self.complexity += self._calculate_function_complexity(node)

            # Detectar clases
            elif isinstance(node, ast.ClassDef):
                self.classes.append(node.name)

        # Complejidad base (heurística simple)
        # Cada 50 nodos del AST = +1 complejidad
        total_nodes = sum(1 for _ in ast.walk(self.tree))
        self.complexity += total_nodes // 50

        logger.info(f"Análisis completado: {len(self.imports)} imports, "
                   f"{len(self.functions)} funciones, {len(self.classes)} clases")

    def _calculate_function_complexity(self, function_node: ast.FunctionDef) -> int:
        """
        Calcular complejidad ciclomática de una función

        Args:
            function_node: Nodo AST de la función

        Returns:
            Complejidad ciclomática (número de caminos de ejecución)
        """
        complexity = 1  # Complejidad base por función

        # Contar estructuras de control que aumentan complejidad
        for node in ast.walk(function_node):
            if isinstance(node, (
                ast.If,        # if/elif
                ast.For,       # for loop
                ast.While,     # while loop
                ast.And,       # and lógico
                ast.Or,        # or lógico
                ast.Try,       # try/except
                ast.With,      # with statement
                ast.ExceptHandler,  # except
            )):
                complexity += 1

        return complexity

    def report(self) -> Dict:
        """
        Generar reporte del análisis

        Returns:
            Diccionario con resultados del análisis
        """
        if self.syntax_error:
            return {
                "success": False,
                "syntax_error": self.syntax_error,
                "imports": [],
                "functions": [],
                "classes": [],
                "complexity": None,
                "lines_of_code": len(self.source_code.splitlines())
            }

        return {
            "success": True,
            "syntax_error": None,
            "imports": list(set(filter(None, self.imports))),  # Únicos y no None
            "functions": self.functions,
            "classes": self.classes,
            "complexity": self.complexity,
            "lines_of_code": len(self.source_code.splitlines()),
            "total_imports": len(set(filter(None, self.imports))),
            "total_functions": len(self.functions),
            "total_classes": len(self.classes)
        }

    def get_summary(self) -> str:
        """
        Obtener resumen legible del análisis

        Returns:
            String con resumen del análisis
        """
        report = self.report()

        if not report["success"]:
            return f"❌ Error de sintaxis: {report['syntax_error']}"

        summary = f"""
📊 Análisis de Código Python
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Imports: {report['total_imports']}
   {', '.join(report['imports'][:5])}{'...' if len(report['imports']) > 5 else ''}

🔧 Funciones: {report['total_functions']}
   {', '.join(report['functions'][:5])}{'...' if len(report['functions']) > 5 else ''}

🏗️  Clases: {report['total_classes']}
   {', '.join(report['classes'][:5])}{'...' if len(report['classes']) > 5 else ''}

📏 Líneas de código: {report['lines_of_code']}
🔄 Complejidad: {report['complexity']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return summary.strip()


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def analyze_code(source_code: str) -> Dict:
    """
    Función auxiliar para analizar código de forma rápida

    Args:
        source_code: Código Python a analizar

    Returns:
        Diccionario con resultados del análisis
    """
    analyzer = CodeAnalyzer(source_code)
    analyzer.analyze()
    return analyzer.report()


def get_code_summary(source_code: str) -> str:
    """
    Función auxiliar para obtener resumen de código

    Args:
        source_code: Código Python a analizar

    Returns:
        String con resumen legible
    """
    analyzer = CodeAnalyzer(source_code)
    analyzer.analyze()
    return analyzer.get_summary()


# ============================================================================
# MAIN (para testing)
# ============================================================================

if __name__ == "__main__":
    # Código de ejemplo para testing
    demo_code = """
import os
import sys
from pathlib import Path

class MiClase:
    def __init__(self):
        self.valor = 0

    def metodo_complejo(self, x):
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    print(i)
        else:
            print("Valor bajo")
        return x * 2

def funcion_simple(a, b):
    return a + b

def funcion_con_try():
    try:
        resultado = 10 / 0
    except ZeroDivisionError:
        print("Error")
    finally:
        print("Fin")

# Código principal
if __name__ == "__main__":
    obj = MiClase()
    print(obj.metodo_complejo(15))
"""

    print("=" * 70)
    print("TEST DE ANALIZADOR DE CÓDIGO")
    print("=" * 70)

    # Crear analizador
    analyzer = CodeAnalyzer(demo_code)

    # Analizar
    analyzer.analyze()

    # Mostrar resumen
    print(analyzer.get_summary())

    # Mostrar reporte completo
    print("\n📋 Reporte completo:")
    print("-" * 70)
    report = analyzer.report()
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Test con código con error de sintaxis
    print("\n\n" + "=" * 70)
    print("TEST CON CÓDIGO CON ERROR DE SINTAXIS")
    print("=" * 70)

    bad_code = """
def funcion_mala(
    print("falta cerrar paréntesis"
"""

    analyzer2 = CodeAnalyzer(bad_code)
    analyzer2.analyze()
    print(analyzer2.get_summary())
