#!/usr/bin/env python3

"""
Script para executar todos os testes do PostgreSQL MCP.
"""

import os
import sys
import subprocess
import argparse

def run_tests(standalone=False, unit=False, integration=False, all_tests=False, verbose=False):
    """Executa testes usando pytest.
    
    Args:
        standalone: Se True, executa apenas os testes standalone.
        unit: Se True, executa apenas os testes unitários.
        integration: Se True, executa apenas os testes de integração.
        all_tests: Se True, executa todos os testes.
        verbose: Se True, executa pytest com verbose.
    
    Returns:
        int: Código de retorno (0 para sucesso, não-zero para falha)
    """
    # Adiciona o diretório src ao Python path
    sys.path.insert(0, os.path.abspath("src"))
    
    # Se standalone, usa o diretório standalone_tests
    if standalone and not any([unit, integration, all_tests]):
        cmd = ["cd", "standalone_tests", "&&", "pytest"]
        if verbose:
            cmd.append("-v")
        cmd_str = " ".join(cmd)
        print(f"Executando comando: {cmd_str}")
        return subprocess.run(cmd_str, shell=True).returncode
    
    # Caso contrário, executa os testes normais
    cmd = ["pytest"]
    
    # Adiciona flags baseadas nos argumentos
    if verbose:
        cmd.append("-v")
    
    # Seleciona quais testes executar
    markers = []
    if unit and not all_tests:
        markers.append("unit")
    if integration and not all_tests:
        markers.append("integration")
    
    # Se markers estiver vazio e all_tests for False, assume testes unitários
    if not markers and not all_tests:
        markers.append("unit")
    
    # Adiciona markers ao comando se necessário
    if markers and not all_tests:
        cmd.append("-m")
        cmd.append(" or ".join(markers))
    
    print(f"Executando comando: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Executa testes do PostgreSQL MCP")
    parser.add_argument("--standalone", action="store_true", help="Executa testes standalone")
    parser.add_argument("--unit", action="store_true", help="Executa testes unitários")
    parser.add_argument("--integration", action="store_true", help="Executa testes de integração")
    parser.add_argument("--all", action="store_true", help="Executa todos os testes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Executa com output verboso")
    
    args = parser.parse_args()
    
    return run_tests(
        standalone=args.standalone,
        unit=args.unit,
        integration=args.integration,
        all_tests=args.all,
        verbose=args.verbose
    )

if __name__ == "__main__":
    sys.exit(main()) 