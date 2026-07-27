"""
============================================================
 NVIDIA ShadowForge Agent - Chart Engine
 Arquivo: hacker_tools/reporting/charts.py
============================================================
 Geração de visualizações gráficas profissionais para
 relatórios de pentest: radar de severidade, timeline,
 gráficos de CVSS e heatmap de vulnerabilidades.
============================================================
"""

from __future__ import annotations

import base64
import io
import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger("shadowforge.reporting.charts")

if TYPE_CHECKING:
    pass


class ChartEngine:
    """Motor de gráficos para relatórios de pentest."""

    @staticmethod
    def _check_matplotlib() -> Any:
        """Importa matplotlib sob demanda."""
        try:
            import matplotlib
            matplotlib.use("Agg")  # Headless
            import matplotlib.pyplot as plt
            return plt
        except ImportError:
            logger.warning("matplotlib não disponível - gráficos serão placeholders")
            return None

    @classmethod
    def radar_severidade(cls, vulns: list) -> str:
        """Gera gráfico radar de severidade e retorna base64."""
        plt = cls._check_matplotlib()
        if not plt:
            return ""

        try:
            import numpy as np

            severidades = {"info": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
            for v in vulns:
                sev = v.severidade.value if hasattr(v.severidade, "value") else str(v.severidade)
                severidades[sev] = severidades.get(sev, 0) + 1

            categorias = list(severidades.keys())
            valores = list(severidades.values())

            # Close the radar
            categorias_plot = categorias + [categorias[0]]
            valores_plot = valores + [valores[0]]

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            angulos = np.linspace(0, 2 * np.pi, len(categorias), endpoint=False).tolist()
            angulos += angulos[:1]

            ax.plot(angulos, valores_plot, "o-", color="#0ff", linewidth=2, label="Vulnerabilidades")
            ax.fill(angulos, valores_plot, alpha=0.2, color="#0ff")
            ax.set_xticks(angulos[:-1])
            ax.set_xticklabels(categorias, size=9)
            ax.set_title("Distribuição de Severidade", pad=15, color="white")
            fig.patch.set_facecolor("#0a0a0f")
            ax.set_facecolor("#111")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120, facecolor="#0a0a0f")
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode()

        except Exception as e:
            logger.error("Erro radar: %s", e)
            return ""

    @classmethod
    def timeline_eventos(cls, acoes: list) -> str:
        """Gera timeline de eventos da campanha."""
        plt = cls._check_matplotlib()
        if not plt:
            return ""

        try:
            import numpy as np

            # Simula distribuição de eventos por fase
            fases = ["RECON", "SCAN", "ENUM", "EXPLOIT", "POST", "REPORT"]
            counts = [0] * len(fases)
            for a in acoes:
                # Map ação para fase aproximada
                tipo = a.tipo if hasattr(a, "tipo") else ""
                if "recon" in tipo.lower():
                    counts[0] += 1
                elif "scan" in tipo.lower():
                    counts[1] += 1
                elif "enum" in tipo.lower():
                    counts[2] += 1
                elif "exploit" in tipo.lower():
                    counts[3] += 1
                elif "post" in tipo.lower():
                    counts[4] += 1
                elif "report" in tipo.lower():
                    counts[5] += 1

            fig, ax = plt.subplots(figsize=(10, 4))
            pos = np.arange(len(fases))
            bars = ax.bar(pos, counts, color=["#0ff", "#00ff41", "#ffd700", "#ff6600", "#ff0040", "#8800ff"])
            ax.set_xticks(pos)
            ax.set_xticklabels(fases, rotation=0)
            ax.set_ylabel("Ações", color="white")
            ax.set_title("Timeline da Campanha", color="white")
            fig.patch.set_facecolor("#0a0a0f")
            ax.set_facecolor("#111")
            ax.tick_params(colors="white")
            ax.spines["bottom"].set_color("#333")
            ax.spines["left"].set_color("#333")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120, facecolor="#0a0a0f")
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode()

        except Exception as e:
            logger.error("Erro timeline: %s", e)
            return ""

    @classmethod
    def heatmap_cvss(cls, vulns: list) -> str:
        """Gera heatmap de CVSS médio por categoria."""
        plt = cls._check_matplotlib()
        if not plt:
            return ""

        try:
            import numpy as np
            from collections import defaultdict

            por_tipo: dict[str, list[float]] = defaultdict(list)
            for v in vulns:
                tipo = v.tipo.value if hasattr(v.tipo, "value") else str(v.tipo)
                cvss = v.cvss_score if hasattr(v, "cvss_score") else 0.0
                if cvss > 0:
                    por_tipo[tipo].append(cvss)

            if not por_tipo:
                return ""

            tipos = list(por_tipo.keys())[:10]
            medias = [sum(por_tipo[t]) / len(por_tipo[t]) for t in tipos]

            fig, ax = plt.subplots(figsize=(10, 3))
            colors = plt.cm.YlOrRd(np.array(medias) / 10.0)
            bars = ax.barh(range(len(tipos)), medias, color=colors)
            ax.set_yticks(range(len(tipos)))
            ax.set_yticklabels(tipos)
            ax.set_xlabel("CVSS Médio", color="white")
            ax.set_xlim(0, 10)
            ax.set_title("CVSS Médio por Categoria", color="white")
            fig.patch.set_facecolor("#0a0a0f")
            ax.set_facecolor("#111")
            ax.tick_params(colors="white")

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120, facecolor="#0a0a0f")
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode()

        except Exception as e:
            logger.error("Erro heatmap: %s", e)
            return ""
