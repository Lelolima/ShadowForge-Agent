"""
============================================================
 NVIDIA ShadowForge Agent - PDF Exporter
 Arquivo: hacker_tools/reporting/pdf_exporter.py
============================================================
 Exporta relatórios para PDF profissional com estilo
cyberpunk/hacker usando ReportLab.
============================================================
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("shadowforge.reporting.pdf")


class PDFExporter:
    """Exportador de relatórios para PDF."""

    CYBERPUNK_COLORS = {
        "bg": "#0a0a0f",
        "fg": "#00ff41",
        "accent": "#0ff",
        "red": "#ff0040",
        "yellow": "#ffd700",
        "white": "#fff",
    }

    @classmethod
    def export(cls, relatorio: dict[str, Any], caminho: str) -> str:
        """Exporta relatório para PDF e retorna caminho."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
            )

            # Document
            doc = SimpleDocTemplate(caminho, pagesize=A4,
                                     rightMargin=2 * cm, leftMargin=2 * cm,
                                     topMargin=2 * cm, bottomMargin=2 * cm)
            elements: list[Any] = []
            styles = getSampleStyleheet()

            # Título
            titulo_style = ParagraphStyle(
                "TítuloH1",
                parent=styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#00ff41"),
                alignment=1,
                spaceAfter=20,
            )
            elements.append(Paragraph("ShadowForge Report", titulo_style))
            elements.append(Spacer(1, 0.5 * cm))

            # Meta info
            meta = relatorio.get("meta", {})
            meta_data = [
                ["Campanha:", meta.get("campanha_id", "N/A")],
                ["Data:", meta.get("data", datetime.now().isoformat())],
                ["Agente:", meta.get("agente", "ShadowForge")],
            ]
            meta_table = Table(meta_data, colWidths=[4 * cm, 10 * cm])
            meta_table.setStyle(TableStyle([
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#00ff41")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 1 * cm))

            # Resumo executivo
            resumo = relatorio.get("resumo_executivo", {})
            elements.append(Paragraph("<b>Resumo Executivo</b>", styles["Heading2"]))
            elements.append(Paragraph(resumo.get("conclusao", ""), styles["BodyText"]))
            elements.append(Spacer(1, 0.5 * cm))

            # Tabela de vulnerabilidades
            vulns = relatorio.get("vulnerabilidades", [])
            if vulns:
                elements.append(Paragraph("<b>Vulnerabilidades</b>", styles["Heading2"]))
                vuln_data = [["ID", "Título", "Tipo", "CVSS", "Severidade"]]
                for v in vulns[:50]:
                    vuln_data.append([
                        v.get("id", ""),
                        v.get("titulo", ""),
                        v.get("tipo", ""),
                        str(v.get("cvss_score", "")),
                        v.get("severidade", ""),
                    ])
                vuln_table = Table(vuln_data, colWidths=[3 * cm, 8 * cm, 3 * cm, 2 * cm, 3 * cm])
                vuln_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#333")),
                    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ]))
                elements.append(vuln_table)

            # Build PDF
            doc.build(elements)
            logger.info("PDF exportado: %s", caminho)
            return caminho

        except ImportError:
            logger.warning("reportlab não disponível - PDF não gerado")
            return ""
        except Exception as e:
            logger.error("Erro ao exportar PDF: %s", e)
            return ""
