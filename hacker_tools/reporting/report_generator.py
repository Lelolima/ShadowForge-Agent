"""
============================================================
 NVIDIA ShadowForge Agent - Gerador de Relatórios
 Arquivo: hacker_tools/reporting/report_generator.py
============================================================
 Relatório profissional de pentest com CVSS, PoCs,
 recomendações de remediação e export multi-formato.
 Estilo visual cyberpunk/hacker nos templates.
============================================================
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("shadowforge.tools.reporting")


class ReportGenerator:
    """Gerador de relatórios profissionais de pentest.

    Gera relatórios completos a partir do estado da campanha,
    com resumo executivo, metodologia, vulnerabilidades
    detalhadas, scores CVSS e recomendações.

    Exporta em Markdown, JSON e HTML com estilo cyberpunk.
    """

    def __init__(self) -> None:
        self._template_dir = Path(__file__).parent / "templates"

    async def gerar(self, estado: Any) -> dict[str, Any]:
        """Gera relatório completo a partir do EstadoAgente.

        Args:
            estado: EstadoAgente com dados da campanha

        Returns:
            Dicionário com relatório completo
        """
        resumo = estado.resumo()

        # Cabeçalho
        relatorio: dict[str, Any] = {
            "meta": {
                "titulo": "Relatório de Teste de Intrusão",
                "agente": "NVIDIA ShadowForge Agent (SH4D0WF0RG3)",
                "versao": "1.0.0",
                "data": datetime.now().isoformat(),
                "campanha_id": estado.campanha_id,
                "metodologia": "OWASP Testing Guide v4 + PTES + MITRE ATT&CK",
            },
            "resumo_executivo": self._gerar_resumo_executivo(estado),
            "escopo": self._gerar_escopo(estado),
            "metodologia": self._gerar_metodologia(),
            "vulnerabilidades": self._detalhar_vulnerabilidades(estado),
            "score_geral": self._calcular_score_geral(estado.vulnerabilidades),
            "recomendacoes": self._gerar_recomendacoes_gerais(estado),
            "risco_residual": self._avaliar_risco_residual(estado),
            "apendices": {
                "ferramentas": ["Nmap", "Nikto", "SQLMap", "ShadowForge Vision"],
                "total_acoes": len(estado.acoes),
                "duracao_min": resumo.get("duracao_min", 0),
            },
        }

        return relatorio

    def _gerar_resumo_executivo(self, estado: Any) -> dict[str, Any]:
        """Gera resumo executivo."""
        _resumo = estado.resumo()  # noqa: F841
        vulns = estado.vulnerabilidades
        crit_count = sum(1 for v in vulns if v.severidade.value == "critical")
        high_count = sum(1 for v in vulns if v.severidade.value == "high")

        nivel_risco = "CRÍTICO" if crit_count > 0 else "ALTO" if high_count > 0 else "MODERADO"

        return {
            "objetivo": f"Teste de intrusão autorizado em {estado.alvo_principal or 'escopo definido'}",
            "periodo": f"Início: {estado.inicio.isoformat()} | Fim: {datetime.now().isoformat()}",
            "total_vulnerabilidades": len(vulns),
            "criticas": crit_count,
            "altas": high_count,
            "nivel_risco": nivel_risco,
            "top_3": [
                {
                    "titulo": v.titulo,
                    "severidade": v.severidade.value,
                    "cvss": v.cvss_score,
                }
                for v in sorted(vulns, key=lambda x: x.cvss_score, reverse=True)[:3]
            ],
            "conclusao": (
                f"Foram identificadas {len(vulns)} vulnerabilidades, sendo {crit_count} críticas "
                f"e {high_count} de alta severidade. O nível de risco geral é {nivel_risco}. "
                f"Recomenda-se remediação imediata das vulnerabilidades críticas."
            ),
        }

    def _gerar_escopo(self, estado: Any) -> dict[str, Any]:
        """Gera descrição do escopo."""
        return {
            "alvo_principal": estado.alvo_principal,
            "total_hosts": len(estado.alvos),
            "hosts": [
                {
                    "endereco": h.endereco,
                    "hostname": h.hostname,
                    "portas_abertas": len(h.portas_abertas),
                    "autorizado": h.autorizado,
                }
                for h in estado.alvos[:20]
            ],
            "tipo_teste": "Pentest Black Box / Gray Box",
            "restricoes": "Sem ações destrutivas, sem backdoors, sem exfiltração real",
        }

    def _gerar_metodologia(self) -> dict[str, Any]:
        """Descreve metodologia utilizada."""
        return {
            "frameworks": [
                "OWASP Testing Guide v4.2",
                "PTES (Penetration Testing Execution Standard)",
                "NIST SP 800-115",
                "MITRE ATT&CK Framework",
            ],
            "fases": [
                {"fase": "Reconnaissance", "descricao": "Mapeamento de superfície de ataque"},
                {"fase": "Scanning", "descricao": "Identificação de portas e serviços"},
                {"fase": "Enumeration", "descricao": "Coleta detalhada de informações"},
                {"fase": "Exploitation", "descricao": "Validação de vulnerabilidades com PoC"},
                {"fase": "Post-Exploitation", "descricao": "Análise de impacto e escalation"},
                {"fase": "Reporting", "descricao": "Documentação completa de achados"},
            ],
            "ferramentas": [
                "NVIDIA ShadowForge Agent (automação + visão)",
                "Nmap (port scanning)",
                "Nikto (web scanning)",
                "SQLMap (SQL injection)",
                "Nemotron Vision (screen analysis)",
            ],
        }

    def _detalhar_vulnerabilidades(self, estado: Any) -> list[dict[str, Any]]:
        """Detalha cada vulnerabilidade encontrada."""
        detalhes = []
        for vuln in estado.vulnerabilidades:
            detalhes.append({
                "id": vuln.id,
                "titulo": vuln.titulo,
                "tipo": vuln.tipo.value,
                "severidade": vuln.severidade.value,
                "cvss_score": vuln.cvss_score,
                "cvss_range": vuln.severidade.cvss_range,
                "cve_id": vuln.cve_id,
                "descricao": vuln.descricao,
                "localizacao": vuln.localizacao,
                "prova_de_conceito": vuln.prova_conceito if vuln.explorada else "[PoC gerado - requer validação manual]",
                "impacto": self._avaliar_impacto(vuln),
                "remediacao": self._gerar_recomendacao(vuln),
                "referencias": self._gerar_referencias(vuln),
                "explorada": vuln.explorada,
                "timestamp": vuln.timestamp,
            })
        return detalhes

    def _avaliar_impacto(self, vuln: Any) -> dict[str, str]:
        """Avalia impacto CIA (Confidentiality, Integrity, Availability)."""
        impactos_por_tipo = {
            "sql_injection": {"c": "ALTO", "i": "ALTO", "d": "MÉDIO"},
            "xss_reflected": {"c": "MÉDIO", "i": "MÉDIO", "d": "BAIXO"},
            "xss_stored": {"c": "ALTO", "i": "ALTO", "d": "MÉDIO"},
            "csrf": {"c": "BAIXO", "i": "MÉDIO", "d": "BAIXO"},
            "ssrf": {"c": "ALTO", "i": "MÉDIO", "d": "BAIXO"},
            "broken_authentication": {"c": "ALTO", "i": "ALTO", "d": "BAIXO"},
            "privilege_escalation": {"c": "ALTO", "i": "ALTO", "d": "ALTO"},
            "information_disclosure": {"c": "MÉDIO", "i": "BAIXO", "d": "BAIXO"},
        }
        return impactos_por_tipo.get(vuln.tipo.value, {"c": "MÉDIO", "i": "MÉDIO", "d": "MÉDIO"})

    def _gerar_recomendacao(self, vuln: Any) -> str:
        """Gera recomendação de remediação para a vulnerabilidade."""
        recomendacoes = {
            "sql_injection": (
                "1. Use prepared statements/parameterized queries\n"
                "2. Implemente input validation no server-side\n"
                "3. Aplique principle of least privilege no banco\n"
                "4. Implemente WAF com regras anti-SQLi\n"
                "5. Realize code review nas queries dinâmicas"
            ),
            "xss_reflected": (
                "1. Sanitize todo input do usuário (HTML encoding)\n"
                "2. Implemente Content Security Policy (CSP)\n"
                "3. Use frameworks com auto-escaping (React, Angular)\n"
                "4. Valide input no server-side\n"
                "5. Adicione HttpOnly e Secure flags nos cookies"
            ),
            "xss_stored": (
                "1. Sanitize dados antes de armazenar no banco\n"
                "2. Encode output baseado no contexto (HTML, JS, URL)\n"
                "3. Implemente CSP restritiva\n"
                "4. Use DOMPurify ou similar para sanitização\n"
                "5. Revise todos os pontos de renderização de user input"
            ),
            "csrf": (
                "1. Implemente tokens anti-CSRF em todos os forms\n"
                "2. Verifique header Origin/Referer\n"
                "3. Use SameSite cookie attribute\n"
                "4. Reautenticação para ações críticas\n"
                "5. Considere double-submit cookie pattern"
            ),
            "broken_authentication": (
                "1. Implemente MFA (multi-factor authentication)\n"
                "2. Use rate limiting e account lockout\n"
                "3. Implemente password policy forte\n"
                "4. Use bcrypt/argon2 para hash de senhas\n"
                "5. Revise session management (timeout, rotation)"
            ),
            "privilege_escalation": (
                "1. Aplique principle of least privilege\n"
                "2. Revise permissões de SUID/SGID binaries\n"
                "3. Mantenha kernel e software atualizados\n"
                "4. Implemente SELinux/AppArmor mandatory access control\n"
                "5. Monitore tentativas de privesc via SIEM"
            ),
            "information_disclosure": (
                "1. Remova arquivos de info (phpinfo.php, readme.html)\n"
                "2. Desabilite directory listing\n"
                "3. Configure error pages customizadas\n"
                "4. Revise headers HTTP (X-Powered-By, Server)\n"
                "5. Implemente access control em endpoints sensíveis"
            ),
        }
        return recomendacoes.get(vuln.tipo.value, "1. Investigue a vulnerabilidade\n2. Aplique correções específicas\n3. Valide a remediação")

    def _gerar_referencias(self, vuln: Any) -> list[str]:
        """Gera referências CWE/CVE/OWASP para a vulnerabilidade."""
        refs_por_tipo = {
            "sql_injection": ["CWE-89", "OWASP A03:2021", "MITRE T1190"],
            "xss_reflected": ["CWE-79", "OWASP A03:2021", "MITRE T1059"],
            "xss_stored": ["CWE-79", "OWASP A03:2021", "MITRE T1059"],
            "csrf": ["CWE-352", "OWASP A01:2021"],
            "ssrf": ["CWE-918", "OWASP A10:2021", "MITRE T1190"],
            "broken_authentication": ["CWE-287", "OWASP A07:2021", "MITRE T1110"],
            "privilege_escalation": ["CWE-269", "MITRE T1548", "MITRE T1068"],
            "information_disclosure": ["CWE-200", "OWASP A01:2021"],
        }
        refs = refs_por_tipo.get(vuln.tipo.value, [])
        if vuln.cve_id:
            refs.append(vuln.cve_id)
        return refs

    def _calcular_score_geral(self, vulnerabilidades: list) -> float:
        """Calcula score geral de risco (0-10).

        Baseado em CVSS médio ponderado com peso
        maior para vulnerabilidades críticas.
        """
        if not vulnerabilidades:
            return 0.0

        pesos = {"critical": 4.0, "high": 2.0, "medium": 1.0, "low": 0.3, "info": 0.05}
        score_total = 0.0
        peso_total = 0.0

        for vuln in vulnerabilidades:
            peso = pesos.get(vuln.severidade.value, 0.1)
            score_total += vuln.cvss_score * peso
            peso_total += peso

        if peso_total == 0:
            return 0.0

        score_medio = score_total / peso_total
        return round(min(10.0, score_medio), 1)

    def _gerar_recomendacoes_gerais(self, estado: Any) -> list[str]:
        """Gera recomendações gerais de segurança."""
        recs = [
            "Implementar programa de segurança contínuo (não apenas pentest puntual)",
            "Estabelecer processo de triagem e remediação com SLAs por severidade",
            "Realizar testes de intrusão regulares (mínimo trimestral)",
            "Implementar WAF/IDS para proteção em tempo real",
            "Estabelecer política de hardening para novos deployments",
        ]
        if any(v.severidade.value == "critical" for v in estado.vulnerabilidades):
            recs.insert(0, "PRIORIDADE MÁXIMA: Corrigir vulnerabilidades CRÍTICAS imediatamente")
        return recs

    def _avaliar_risco_residual(self, estado: Any) -> dict[str, Any]:
        """Avalia risco residual após remediação."""
        return {
            "pos_remediacao": "MÉDIO - Algumas vulnerabilidades requerem mudanças arquiteturais",
            "recomendacoes_adicionais": [
                "Implementar SDL (Security Development Lifecycle)",
                "Treinamento de desenvolvedores em secure coding",
                "Implementar SAST/DAST no pipeline CI/CD",
                "Bug bounty program para descoberta contínua",
            ],
        }

    # === Exportadores ===

    def exportar_markdown(self, relatorio: dict[str, Any]) -> str:
        """Exporta relatório em Markdown."""
        md = "# Relatório de Teste de Intrusão\n\n"
        md += f"**Agente:** {relatorio['meta']['agente']}\n"
        md += f"**Data:** {relatorio['meta']['data']}\n"
        md += f"**Campanha:** {relatorio['meta']['campanha_id']}\n\n"

        # Resumo executivo
        re = relatorio["resumo_executivo"]
        md += "## Resumo Executivo\n\n"
        md += f"{re['conclusao']}\n\n"
        md += f"- **Total de vulnerabilidades:** {re['total_vulnerabilidades']}\n"
        md += f"- **Críticas:** {re['criticas']}\n"
        md += f"- **Altas:** {re['altas']}\n"
        md += f"- **Nível de risco:** {re['nivel_risco']}\n"
        md += f"- **Score geral:** {relatorio['score_geral']}/10\n\n"

        # Vulnerabilidades
        md += "## Vulnerabilidades\n\n"
        for v in relatorio.get("vulnerabilidades", []):
            sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
            emoji = sev_emoji.get(v["severidade"], "⚪")
            md += f"### {emoji} [{v['severidade'].upper()}] {v['titulo']}\n\n"
            md += f"- **ID:** {v['id']}\n"
            md += f"- **Tipo:** {v['tipo']}\n"
            md += f"- **CVSS:** {v['cvss_score']}\n"
            md += f"- **Localização:** {v['localizacao']}\n"
            if v.get("cve_id"):
                md += f"- **CVE:** {v['cve_id']}\n"
            md += f"\n**Descrição:** {v['descricao']}\n\n"
            md += f"**Impacto CIA:** C={v['impacto']['c']} | I={v['impacto']['i']} | D={v['impacto']['d']}\n\n"
            md += f"**Remediação:**\n```\n{v['remediacao']}\n```\n\n"
            md += f"**Referências:** {', '.join(v['referencias'])}\n\n---\n\n"

        # Recomendações
        md += "## Recomendações Gerais\n\n"
        for i, rec in enumerate(relatorio.get("recomendacoes", []), 1):
            md += f"{i}. {rec}\n"

        md += "\n---\n*Gerado automaticamente por SH4D0WF0RG3*\n"
        return md

    def exportar_json(self, relatorio: dict[str, Any]) -> str:
        """Exporta relatório em JSON formatado."""
        return json.dumps(relatorio, indent=2, ensure_ascii=False, default=str)

    def exportar_html(self, relatorio: dict[str, Any]) -> str:
        """Exporta relatório em HTML com estilo cyberpunk."""
        html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShadowForge - Relatório de Pentest</title>
<style>
:root { --bg: #0a0a0f; --text: #00ff41; --accent: #0ff; --red: #ff0040; --yellow: #ffd700; --blue: #0088ff; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; padding: 2rem; }
.container { max-width: 1200px; margin: 0 auto; }
h1 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 1rem; margin-bottom: 2rem; text-shadow: 0 0 10px var(--accent); }
h2 { color: var(--text); margin: 2rem 0 1rem; }
h3 { color: var(--accent); margin: 1.5rem 0 0.5rem; }
.card { background: #111; border: 1px solid #333; border-radius: 4px; padding: 1.5rem; margin: 1rem 0; }
.critical { border-left: 4px solid var(--red); }
.high { border-left: 4px solid #ff6600; }
.medium { border-left: 4px solid var(--yellow); }
.low { border-left: 4px solid var(--blue); }
.cvss { font-size: 2rem; font-weight: bold; }
.cvss.high { color: var(--red); }
.cvss.medium { color: var(--yellow); }
.cvss.low { color: var(--blue); }
pre { background: #000; padding: 1rem; border-radius: 4px; overflow-x: auto; border: 1px solid #222; }
code { color: var(--accent); }
.score { font-size: 4rem; text-align: center; color: var(--red); text-shadow: 0 0 20px var(--red); }
.label { color: #888; font-size: 0.85rem; text-transform: uppercase; }
.value { color: var(--text); }
.ref { color: var(--blue); }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #333; color: #555; font-size: 0.8rem; text-align: center; }
</style>
</head>
<body>
<div class="container">
<h1>&#x1F4CB; Relatório de Teste de Intrusão</h1>
"""
        # Resumo
        re = relatorio["resumo_executivo"]
        html += f"""<div class="card">
<h2>Resumo Executivo</h2>
<p>{re['conclusao']}</p>
<p><span class="label">Vulnerabilidades:</span> <span class="value">{re['total_vulnerabilidades']}</span> |
<span class="label">Críticas:</span> <span class="value" style="color:var(--red)">{re['criticas']}</span> |
<span class="label">Altas:</span> <span class="value" style="color:#ff6600">{re['altas']}</span></p>
<p><span class="label">Nível de Risco:</span> <span class="value" style="color:var(--red);font-weight:bold">{re['nivel_risco']}</span></p>
<div class="score">{relatorio['score_geral']}/10</div>
</div>
"""

        # Vulnerabilidades
        html += "<h2>Vulnerabilidades</h2>\n"
        for v in relatorio.get("vulnerabilidades", []):
            html += f"""<div class="card {v['severidade']}">
<h3>[{v['severidade'].upper()}] {v['titulo']}</h3>
<p><span class="label">CVSS:</span> <span class="cvss {v['severidade']}">{v['cvss_score']}</span> |
<span class="label">Tipo:</span> <span class="value">{v['tipo']}</span> |
<span class="label">Localização:</span> <span class="value">{v['localizacao']}</span></p>
<p><span class="label">Impacto:</span> C={v['impacto']['c']} | I={v['impacto']['i']} | D={v['impacto']['d']}</p>
<p><strong>Descrição:</strong> {v['descricao']}</p>
<pre><code>{v['remediacao']}</code></pre>
<p><span class="label">Referências:</span> <span class="ref">{', '.join(v['referencias'])}</span></p>
</div>\n"""

        # Recomendações
        html += "<div class='card'><h2>Recomendações</h2><ol>\n"
        for rec in relatorio.get("recomendacoes", []):
            html += f"<li>{rec}</li>\n"
        html += "</ol></div>\n"

        html += f"""<footer>
Gerado por SH4D0WF0RG3 | {relatorio['meta']['data']} | Campanha: {relatorio['meta']['campanha_id']}
<br>Ethics first, hack second.
</footer>
</div></body></html>"""
        return html

    async def salvar_em_arquivo(
        self,
        relatorio: dict[str, Any],
        diretorio: str = "data/campaigns",
        formatos: list[str] | None = None,
    ) -> dict[str, str]:
        """Salva relatório em múltiplos formatos.

        Args:
            relatorio: Relatório gerado
            diretorio: Diretório de saída
            formatos: Lista de formatos ["md", "json", "html"]

        Returns:
            Dicionário {formato: caminho_arquivo}
        """
        formatos = formatos or ["md", "json", "html"]
        dir_path = Path(diretorio)
        dir_path.mkdir(parents=True, exist_ok=True)

        cam_id = relatorio.get("meta", {}).get("campanha_id", "unknown")
        arquivos = {}

        if "md" in formatos:
            path = dir_path / f"report_{cam_id}.md"
            path.write_text(self.exportar_markdown(relatorio), encoding="utf-8")
            arquivos["markdown"] = str(path)

        if "json" in formatos:
            path = dir_path / f"report_{cam_id}.json"
            path.write_text(self.exportar_json(relatorio), encoding="utf-8")
            arquivos["json"] = str(path)

        if "html" in formatos:
            path = dir_path / f"report_{cam_id}.html"
            path.write_text(self.exportar_html(relatorio), encoding="utf-8")
            arquivos["html"] = str(path)

        logger.info("Relatório salvo: %d formatos em %s", len(arquivos), diretorio)
        return arquivos
