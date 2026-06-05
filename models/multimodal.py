"""
============================================================
NVIDIA ShadowForge Agent - Nemotron Multimodal
Arquivo: models/multimodal.py
============================================================
Wrapper para Nemotron 3 Nano Omni com processamento
de imagens de tela e chain-of-thought visual-tático.
============================================================
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import ShadowForgeConfig

logger = logging.getLogger("shadowforge.models.multimodal")


class NemotronVision:
    """Processamento visual com Nemotron multimodal.

    Análise de screenshots, detecção de elementos UI,
    chain-of-thought visual-tático para decisões de pentest.
    Integração com NIM para inferência otimizada.

    H-09 FIX: Agora inicializa NIMClient via lazy init (como ScreenUnderstanding).
    """

    # Prompt base para análise visual de pentest
    PROMPT_ANALISE = (
        "Você é o sistema visual do SH4D0WF0RG3, um agente autônomo de pentest ético.\n"
        "Analise esta captura de tela com precisão cirúrgica:\n\n"
        "1. AMBIENTE: Tipo de interface, sistema operacional, ferramentas visíveis\n"
        "2. CONTEÚDO: Texto, códigos, outputs, dados sensíveis visíveis\n"
        "3. OPORTUNIDADES: Elementos exploráveis, vulnerabilidades aparentes, "
        "informações úteis para pentest (IPs, versões, configurações)\n"
        "4. INTERAÇÃO: Elementos clicáveis, formulários, campos de input\n"
        "5. AÇÃO TÁTICA: Próximo passo recomendado para o agente\n\n"
        "Seja preciso, técnico e direto. Formate como JSON."
    )

    def __init__(self, config: ShadowForgeConfig | None = None) -> None:
        self._config = config
        self._modelo = "nvidia/nemotron-3-nano-omni-vl"
        self._nim_client = None  # Será inicializado via lazy init

    def _get_nim_client(self) -> Any:
        """H-09 FIX: Inicialização lazy do NIMClient (como ScreenUnderstanding faz)."""
        if self._nim_client is None:
            try:
                from models.nim_client import NIMClient
                self._nim_client = NIMClient(config=self._config)
                logger.info("NIMClient inicializado para NemotronVision")
            except Exception as e:
                logger.warning("Falha ao inicializar NIMClient para NemotronVision: %s", e)
        return self._nim_client

    async def analisar_tela(self, imagem_base64: str, contexto: str = "") -> dict[str, Any]:
        """Análise completa de screenshot.

        Args:
            imagem_base64: Screenshot em base64
            contexto: Contexto adicional (fase atual, alvo, etc.)

        Returns:
            Dicionário estruturado com análise
        """
        prompt = self.PROMPT_ANALISE
        if contexto:
            prompt += f"\n\nCONTEXTO DA CAMPANHA: {contexto}"

        nim = self._get_nim_client()  # H-09 FIX: usar lazy init
        if nim:
            try:
                resposta = await nim.chamada_multimodal(
                    modelo=self._modelo,
                    texto=prompt,
                    imagem_base64=imagem_base64,
                )
                return self._parsear_analise(resposta)
            except Exception as e:
                logger.error("Erro análise Nemotron: %s", e)

        return {"status": "fallback", "analise": "NIM indisponível"}

    async def chain_of_thought_visual(
        self, imagem_base64: str, objetivo: str
    ) -> list[dict[str, str]]:
        """Chain-of-thought visual-tático para pentest.

        Processa screenshot com raciocínio passo-a-passo
        orientado ao objetivo tático.

        Args:
            imagem_base64: Screenshot
            objetivo: Objetivo tático (ex: "encontrar SQLi")

        Returns:
            Lista de passos de raciocínio
        """
        prompt = (
            f"OBJETIVO TÁTICO: {objetivo}\n\n"
            "Analise esta tela usando raciocínio passo-a-passo:\n"
            "PASSO 1 - Observação: O que vejo na tela?\n"
            "PASSO 2 - Orientação: Como isso se relaciona com o objetivo?\n"
            "PASSO 3 - Decisão: Qual ação tomar?\n"
            "PASSO 4 - Ação: Como executar esta ação?\n\n"
            "Para cada passo, forneça detalhes específicos e acionáveis."
        )

        nim = self._get_nim_client()  # H-09 FIX: usar lazy init
        if nim:
            resposta = await nim.chamada_multimodal(
                modelo=self._modelo,
                texto=prompt,
                imagem_base64=imagem_base64,
                temperatura=0.4,
            )

            # Parseia passos
            passos = []
            for linha in resposta.split("\n"):
                linha = linha.strip()
                if linha.startswith("PASSO"):
                    partes = linha.split(" - ", 1)
                    if len(partes) == 2:
                        passos.append({
                            "passo": partes[0].strip(),
                            "analise": partes[1].strip(),
                        })

            return passos if passos else [{"passo": "completo", "analise": resposta}]

        return [{"passo": "fallback", "analise": "NIM indisponível"}]

    async def detectar_anomalias(self, imagem_base64: str) -> list[dict[str, str]]:
        """Detecta anomalias visuais (erros, alertas, warnings)."""
        prompt = (
            "Analise esta tela e identifique ANOMALIAS visuais:\n"
            "- Mensagens de erro (vermelho, amarelo)\n"
            "- Alertas de segurança\n"
            "- Stack traces\n"
            "- Access denied / Forbidden\n"
            "- Qualquer indicação de falha ou bloqueio\n\n"
            "Retorne em JSON: {\"anomalias\": [{\"tipo\": \"\", \"descricao\": \"\", \"posicao\": \"\"}]}"
        )

        nim = self._get_nim_client()  # H-09 FIX: usar lazy init
        if nim:
            resposta = await nim.chamada_multimodal(
                modelo=self._modelo, texto=prompt, imagem_base64=imagem_base64,
            )
            try:
                import json
                if "{" in resposta:
                    return json.loads(resposta[resposta.index("{"):resposta.rindex("}") + 1]).get("anomalias", [])
            except Exception:
                pass

        return []

    def _parsear_analise(self, resposta: str) -> dict[str, Any]:
        """Parseia resposta da análise em estrutura."""
        import json
        try:
            if "{" in resposta and "}" in resposta:
                return json.loads(resposta[resposta.index("{"):resposta.rindex("}") + 1])
        except (json.JSONDecodeError, ValueError):
            pass
        return {"resposta_bruta": resposta}
