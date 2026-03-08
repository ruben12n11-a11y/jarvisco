#!/usr/bin/env bash
set -e

# 🔹 Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 🔹 Actualizar pip, setuptools y wheel
pip install --upgrade pip setuptools wheel

# 🔹 Instalar dependencias principales
pip install torch \
            transformers==4.44.0 \
            tokenizers==0.19.1 \
            tqdm \
            numpy \
            pandas \
            sentencepiece \
            wandb   # opcional: para visualización

# 🔹 Dependencias opcionales de HuggingFace (solo para ejemplos)
pip install datasets
