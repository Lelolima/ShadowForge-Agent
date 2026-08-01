"""
Pacote do plugin exemplo_plugin.
"""

from .plugin import ExemploPlugin

# Exportar a classe do plugin para fácil importação
__all__ = ["ExemploPlugin"]

# Metadados do pacote (opcional)
__title__ = "exemplo_plugin"
__description__ = "Plugin de exemplo para ShadowForge Agent"
__version__ = "1.0.0"
__author__ = "Seu Nome"