#!/usr/bin/env python3

"""
Configuração para testes standalone dos filtros e query builder.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para permitir importações relativas
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Marker para testes standalone
def pytest_configure(config):
    """Configuração do pytest."""
    config.addinivalue_line("markers", "standalone: testes standalone para filtros e query builder") 