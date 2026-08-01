#!/usr/bin/env python3.11
"""
Script de build e desenvolvimento para ShadowForge Agent
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Execute um comando e retorna o resultado"""
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Erro: {result.stderr}")
        sys.exit(1)
    return result

def lint():
    """Executa linting no código"""
    print("🔍 Executando linting...")
    # Verifica se temos flake8 ou pylint disponível
    try:
        run_command(["flake8", ".", "--exclude=.git,__pycache__,*.pyc,venv,env,.env"])
        print("✅ Linting concluído com sucesso!")
    except FileNotFoundError:
        try:
            run_command(["pylint", "shadowforge_agent", "--disable=C0114,C0115,C0116"])
            print("✅ Linting concluído com sucesso!")
        except FileNotFoundError:
            print("⚠️  Nenhum linter encontrado. Instale flake8 ou pylint para verificar o código.")

def test():
    """Executa os testes"""
    print("🧪 Executando testes...")
    try:
        result = run_command(["pytest", "tests/", "-v"], check=False)
        if result.returncode == 0:
            print("✅ Todos os testes passaram!")
        else:
            print("❌ Alguns testes falharam.")
            print(result.stdout)
            print(result.stderr)
    except FileNotFoundError:
        print("⚠️  pytest não encontrado. Instale com: pip install pytest")

def format_code():
    """Formata o código usando black"""
    print("🎨 Formatando código com black...")
    try:
        run_command(["black", "."])
        print("✅ Código formatado com sucesso!")
    except FileNotFoundError:
        print("⚠️  black não encontrado. Instale com: pip install black")

def type_check():
    """Executa verificacao de tipos"""
    print("🔍 Executando verificação de tipos...")
    try:
        # Para Python
        run_command(["mypy", ".", "--ignore-missing-imports"])
        print("✅ Verificação de tipos concluída!")
    except FileNotFoundError:
        print("⚠️  mypy não encontrado. Instale com: pip install mypy")

def clean():
    """Limpa arquivos temporários"""
    print("🧹 Limpando arquivos temporários...")
    dirs_to_clean = ["__pycache__", ".pytest_cache", ".mypy_cache", "build", "dist", "*.egg-info"]
    files_to_clean = ["*.pyc", "*.pyo"]

    for pattern in dirs_to_clean:
        for path in Path(".").rglob(pattern):
            if path.is_dir():
                print(f"Removendo diretório: {path}")
                import shutil
                shutil.rmtree(path)

    for pattern in files_to_clean:
        for path in Path(".").rglob(pattern):
            if path.is_file():
                print(f"Removendo arquivo: {path}")
                path.unlink()

    print("✅ Limpeza concluída!")

def dev_server():
    """Inicia o servidor de desenvolvimento"""
    print("🚀 Iniciando servidor de desenvolvimento...")
    try:
        # Tenta iniciar o agente principal
        run_command([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Servidor de desenvolvimento encerrado.")
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")

def main():
    parser = argparse.ArgumentParser(description="Script de build e desenvolvimento para ShadowForge Agent")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando lint
    lint_parser = subparsers.add_parser("lint", help="Executa linting no código")

    # Comando test
    test_parser = subparsers.add_parser("test", help="Executa os testes")

    # Comando format
    format_parser = subparsers.add_parser("format", help="Formata o código")

    # Comando typecheck
    typecheck_parser = subparsers.add_parser("typecheck", help="Executa verificação de tipos")

    # Comando clean
    clean_parser = subparsers.add_parser("clean", help="Limpa arquivos temporários")

    # Comando dev
    dev_parser = subparsers.add_parser("dev", help="Inicia o servidor de desenvolvimento")

    # Comando all (executa tudo)
    all_parser = subparsers.add_parser("all", help="Executa lint, teste, typecheck e format")

    args = parser.parse_args()

    if args.command == "lint":
        lint()
    elif args.command == "test":
        test()
    elif args.command == "format":
        format_code()
    elif args.command == "typecheck":
        type_check()
    elif args.command == "clean":
        clean()
    elif args.command == "dev":
        dev_server()
    elif args.command == "all":
        lint()
        test()
        type_check()
        format_code()
        print("✅ Todas as tarefas concluídas!")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()