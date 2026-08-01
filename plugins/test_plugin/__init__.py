"""
Pacote do plugin test_plugin.
"""

from .plugin import TestPlugin

# Exportar a classe do plugin para fácil importação
__all__ = ["TestPlugin"]

# Metadados do pacote (opcional)
__title__ = "test_plugin"
__description__ = "Plugin de teste para validar o hot-reloader"
__version__ = "0.1.0"
__author__ = "Teste Autor"
