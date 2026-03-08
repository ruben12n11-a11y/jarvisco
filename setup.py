#!/usr/bin/env python3
"""
setup.py – Configuración de instalación para jarvisco.
"""

import logging
from pathlib import Path

from setuptools import find_packages, setup

# ---------------------------------------------------------------------------
# Leer README.md (si existe)
this_dir = Path(__file__).parent
readme_file = this_dir / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

setup(
    name="jarvisco",
    version="1.0.0",
    author="Sergio Alberto Sanchez Echeverria",
    author_email="",
    description="Copiloto Offline Senior para Termux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jarvisco",
    packages=find_packages(),
    package_data={"jarvisco": ["*.gbnf"]},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "torch==2.3.0",
        "requests>=2.28.0",
        "numpy",
        "sentencepiece",
    ],
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=22.0.0", "flake8>=4.0.0"],
    },
    entry_points={"console_scripts": ["jarvisco=jarvisco.__init__:entrypoint"]},
    zip_safe=False,
)
