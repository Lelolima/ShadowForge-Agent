"""
============================================================
 NVIDIA ShadowForge Agent - RAG MITRE ATT&CK
 Arquivo: planning/rag.py
============================================================
 Base de conhecimento MITRE ATT&CK, OWASP, CVEs
 com busca semântica via NVIDIA Embeddings + ChromaDB.
============================================================
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("shadowforge.planning.rag")


class MITRERAG:
    """RAG com base de conhecimento MITRE ATT&CK.

    Armazena e busca técnicas táticas usando ChromaDB
    como vector store e NVIDIA Embeddings para
    representação semântica. Inclui:

    - MITRE ATT&CK: táticas, técnicas, procedimentos
    - OWASP Top 10: categorias e recomendações
    - CVE database: vulnerabilidades conhecidas
    - Busca semântica com similaridade cosseno
    - Suggestion de próximas ações baseado no contexto
    """

    # Conhecimento MITRE ATT&CK pré-carregado (subset)
    MITRE_TECNICAS = [
        {"id": "T1595", "nome": "Active Scanning", "tatica": "Reconnaissance",
         "descricao": "Adversaries may execute active reconnaissance scans to gather information",
         "fase_sh4d0w": "recon", "keywords": ["scan", "nmap", "port", "recon"]},
        {"id": "T1592", "nome": "Gather Victim Host Info", "tatica": "Reconnaissance",
         "descricao": "Adversaries may gather information about the victim's hosts",
         "fase_sh4d0w": "recon", "keywords": ["host", "enumeration", "osint"]},
        {"id": "T1190", "nome": "Exploit Public-Facing App", "tatica": "Initial Access",
         "descricao": "Adversaries may exploit vulnerabilities in public-facing applications",
         "fase_sh4d0w": "exploit", "keywords": ["exploit", "web", "sqli", "xss", "vulnerability"]},
        {"id": "T1110", "nome": "Brute Force", "tatica": "Credential Access",
         "descricao": "Adversaries may use brute force techniques to gain access to accounts",
         "fase_sh4d0w": "exploit", "keywords": ["brute", "force", "password", "credential", "hydra"]},
        {"id": "T1071", "nome": "Application Layer Protocol", "tatica": "Command and Control",
         "descricao": "Adversaries may communicate using application layer protocols",
         "fase_sh4d0w": "post", "keywords": ["c2", "protocol", "http", "dns"]},
        {"id": "T1059", "nome": "Command and Scripting Interpreter", "tatica": "Execution",
         "descricao": "Adversaries may abuse command and script interpreters",
         "fase_sh4d0w": "exploit", "keywords": ["shell", "command", "script", "powershell", "bash"]},
        {"id": "T1068", "nome": "Exploitation for Privilege Escalation", "tatica": "Privilege Escalation",
         "descricao": "Adversaries may exploit software vulnerabilities to elevate privileges",
         "fase_sh4d0w": "post", "keywords": ["privilege", "escalation", "root", "admin", "privesc"]},
        {"id": "T1548", "nome": "Abuse Elevation Control Mechanism", "tatica": "Privilege Escalation",
         "descricao": "Adversaries may bypass mechanisms designed to control elevated access",
         "fase_sh4d0w": "post", "keywords": ["sudo", "suid", "uac", "bypass"]},
        {"id": "T1087", "nome": "Account Discovery", "tatica": "Discovery",
         "descricao": "Adversaries may attempt to get a listing of accounts on a system",
         "fase_sh4d0w": "enum", "keywords": ["account", "user", "discovery", "enum"]},
        {"id": "T1046", "nome": "Network Service Discovery", "tatica": "Discovery",
         "descricao": "Adversaries may attempt to get a listing of services running on remote hosts",
         "fase_sh4d0w": "enum", "keywords": ["service", "network", "discovery", "nmap"]},
        {"id": "T1003", "nome": "OS Credential Dumping", "tatica": "Credential Access",
         "descricao": "Adversaries may attempt to dump credentials to obtain account login info",
         "fase_sh4d0w": "post", "keywords": ["credential", "dump", "mimikatz", "hash", "sam"]},
        {"id": "T1566", "nome": "Phishing", "tatica": "Initial Access",
         "descricao": "Adversaries may use phishing to gain initial access",
         "fase_sh4d0w": "exploit", "keywords": ["phishing", "social", "engineering", "email"]},
    ]

    # OWASP Top 10 2021
    OWASP_TOP10 = [
        {"id": "A01", "nome": "Broken Access Control", "cwe": "CWE-284",
         "descricao": "Failures in access control typically lead to unauthorized information disclosure",
         "tecnicas_mitre": ["T1190", "T1068"], "keywords": ["access", "control", "idor", "unauthorized"]},
        {"id": "A02", "nome": "Cryptographic Failures", "cwe": "CWE-259",
         "descricao": "Failures related to cryptography which often lead to sensitive data exposure",
         "tecnicas_mitre": ["T1110"], "keywords": ["crypto", "encryption", "ssl", "tls", "weak"]},
        {"id": "A03", "nome": "Injection", "cwe": "CWE-79",
         "descricao": "SQL, NoSQL, OS, and LDAP injection vulnerabilities",
         "tecnicas_mitre": ["T1190", "T1059"], "keywords": ["injection", "sql", "xss", "command", "ldap"]},
        {"id": "A04", "nome": "Insecure Design", "cwe": "CWE-209",
         "descricao": "Missing or ineffective security controls in design",
         "tecnicas_mitre": [], "keywords": ["design", "architecture", "flaw"]},
        {"id": "A05", "nome": "Security Misconfiguration", "cwe": "CWE-16",
         "descricao": "Missing security hardening, default configs, open cloud storage",
         "tecnicas_mitre": ["T1190"], "keywords": ["misconfiguration", "default", "hardening", "cors"]},
        {"id": "A06", "nome": "Vulnerable Components", "cwe": "CWE-1104",
         "descricao": "Using components with known vulnerabilities",
         "tecnicas_mitre": ["T1190"], "keywords": ["component", "library", "outdated", "cve"]},
        {"id": "A07", "nome": "Auth Failures", "cwe": "CWE-287",
         "descricao": "Identification and authentication failures",
         "tecnicas_mitre": ["T1110"], "keywords": ["authentication", "auth", "login", "session", "brute"]},
        {"id": "A08", "nome": "Software/Data Integrity Failures", "cwe": "CWE-354",
         "descricao": "Code and infrastructure not protected against integrity violations",
         "tecnicas_mitre": ["T1059"], "keywords": ["integrity", "ci", "cd", "pipeline", "supply"]},
        {"id": "A09", "nome": "Logging Failures", "cwe": "CWE-778",
         "descricao": "Insufficient logging and monitoring",
         "tecnicas_mitre": [], "keywords": ["logging", "monitoring", "audit", "siem"]},
        {"id": "A10", "nome": "SSRF", "cwe": "CWE-918",
         "descricao": "Server-Side Request Forgery flaws",
         "tecnicas_mitre": ["T1190"], "keywords": ["ssrf", "request", "forge", "internal"]},
    ]

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._chroma_dir = "data/chromadb"
        self._embeddings_client = None
        self._chroma_client = None
        self._colecoes: dict[str, Any] = {}
        self._initialized = False

        if config:
            data_dir = getattr(config, "data_dir", None)
            if data_dir:
                self._chroma_dir = str(Path(data_dir) / "chromadb")

    async def inicializar(self) -> None:
        """Inicializa ChromaDB e carrega conhecimento."""
        if self._initialized:
            return

        try:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=self._chroma_dir)

            # Cria coleções
            self._colecoes["mitre"] = self._chroma_client.get_or_create_collection(
                name="mitre_attack", metadata={"description": "MITRE ATT&CK techniques"}
            )
            self._colecoes["owasp"] = self._chroma_client.get_or_create_collection(
                name="owasp_top10", metadata={"description": "OWASP Top 10 2021"}
            )

            # Carrega dados se coleções vazias
            if self._colecoes["mitre"].count() == 0:
                await self.popular_base_conhecimento()

            # Inicializa embeddings NVIDIA
            try:
                from models.embeddings import NVIDIAEmbeddings
                self._embeddings_client = NVIDIAEmbeddings(config=self._config)
            except ImportError:
                logger.warning("NVIDIA Embeddings não disponível, busca por texto")

            self._initialized = True
            logger.info("RAG inicializado: %d MITRE, %d OWASP",
                       self._colecoes["mitre"].count(),
                       self._colecoes["owasp"].count())

        except ImportError:
            logger.warning("ChromaDB não disponível, modo em-memória")
            self._chroma_client = None
            self._initialized = True

    async def popular_base_conhecimento(self) -> None:
        """Carrega conhecimento MITRE e OWASP no ChromaDB."""
        if not self._chroma_client:
            return

        # MITRE
        mitre_docs = []
        mitre_ids = []
        mitre_metas = []
        for t in self.MITRE_TECNICAS:
            mitre_docs.append(f"{t['nome']}: {t['descricao']} Keywords: {' '.join(t['keywords'])}")
            mitre_ids.append(t["id"])
            mitre_metas.append({"tatica": t["tatica"], "fase": t["fase_sh4d0w"]})

        if mitre_docs:
            self._colecoes["mitre"].add(documents=mitre_docs, ids=mitre_ids, metadatas=mitre_metas)

        # OWASP
        owasp_docs = []
        owasp_ids = []
        owasp_metas = []
        for o in self.OWASP_TOP10:
            owasp_docs.append(f"{o['nome']}: {o['descricao']} Keywords: {' '.join(o['keywords'])}")
            owasp_ids.append(o["id"])
            owasp_metas.append({"cwe": o["cwe"], "mitre_refs": ",".join(o.get("tecnicas_mitre", []))})

        if owasp_docs:
            self._colecoes["owasp"].add(documents=owasp_docs, ids=owasp_ids, metadatas=owasp_metas)

        logger.info("Base de conhecimento carregada: %d MITRE + %d OWASP",
                    len(mitre_docs), len(owasp_docs))

    async def buscar_tecnicas(
        self, fase: str = "", alvo: str = "", query: str = "", top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Busca técnicas relevantes para o contexto atual.

        Args:
            fase: Fase da kill chain (recon, exploit, post, etc.)
            alvo: Alvo da operação
            query: Query de busca semântica
            top_k: Número máximo de resultados

        Returns:
            Lista de técnicas relevantes
        """
        if not self._initialized:
            await self.inicializar()

        # Constrói query
        termos = []
        if fase:
            termos.append(fase)
        if alvo:
            termos.append(alvo)
        if query:
            termos.append(query)
        query_text = " ".join(termos) if termos else "general hacking technique"

        resultados = []

        # Busca no MITRE via ChromaDB
        if self._chroma_client and "mitre" in self._colecoes:
            try:
                where_filter = {}
                if fase:
                    where_filter = {"fase": fase}

                query_result = self._colecoes["mitre"].query(
                    query_texts=[query_text],
                    n_results=min(top_k, 10),
                    where=where_filter if where_filter else None,
                )

                if query_result and query_result.get("documents"):
                    for i, doc in enumerate(query_result["documents"][0]):
                        meta = query_result["metadatas"][0][i] if query_result["metadatas"] else {}
                        resultados.append({
                            "id": query_result["ids"][0][i],
                            "descricao": doc,
                            "tatica": meta.get("tatica", ""),
                            "fase": meta.get("fase", ""),
                            "score": 1.0 - query_result["distances"][0][i] if query_result.get("distances") else 0.5,
                        })
            except Exception as e:
                logger.debug("Busca MITRE falhou: %s", e)

        # Fallback: busca em memória
        if not resultados:
            resultados = self._buscar_em_memoria(query_text, fase, top_k)

        return resultados[:top_k]

    async def buscar_owasp(self, tipo_vuln: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Busca informações OWASP para tipo de vulnerabilidade.

        Args:
            tipo_vuln: Tipo da vulnerabilidade (ex: "sql_injection")
            top_k: Resultados máximos

        Returns:
            Lista de informações OWASP
        """
        if not self._initialized:
            await self.inicializar()

        resultados = []

        if self._chroma_client and "owasp" in self._colecoes:
            try:
                query_result = self._colecoes["owasp"].query(
                    query_texts=[tipo_vuln],
                    n_results=top_k,
                )
                if query_result and query_result.get("documents"):
                    for i, doc in enumerate(query_result["documents"][0]):
                        meta = query_result["metadatas"][0][i] if query_result["metadatas"] else {}
                        resultados.append({
                            "id": query_result["ids"][0][i],
                            "descricao": doc,
                            "cwe": meta.get("cwe", ""),
                            "mitre_refs": meta.get("mitre_refs", "").split(",") if meta.get("mitre_refs") else [],
                        })
            except Exception:
                pass

        # Fallback
        if not resultados:
            for item in self.OWASP_TOP10:
                for kw in item["keywords"]:
                    if kw in tipo_vuln.lower():
                        resultados.append({
                            "id": item["id"],
                            "nome": item["nome"],
                            "descricao": item["descricao"],
                            "cwe": item["cwe"],
                        })
                        break

        return resultados[:top_k]

    async def sugerir_proxima_acao(self, contexto: dict[str, Any]) -> dict[str, Any]:
        """Sugere próxima ação baseado no contexto da campanha.

        Args:
            contexto: Contexto atual (fase, resultados, vulnerabilidades)

        Returns:
            Ação sugerida com justificativa
        """
        fase = contexto.get("fase", "recon")
        _vulns = contexto.get("vulnerabilidades", [])

        tecnicas = await self.buscar_tecnicas(fase=fase, top_k=3)

        sugestoes = {
            "recon": {
                "acao": "port_scan",
                "descricao": "Executar scan de portas para mapear superfície de ataque",
                "ferramenta": "nmap -sV -sC",
                "mitre": tecnicas[0]["id"] if tecnicas else "T1595",
            },
            "scan": {
                "acao": "service_enum",
                "descricao": "Enumerar serviços detectados e identificar versões vulneráveis",
                "ferramenta": "nmap --script=vuln",
                "mitre": tecnicas[0]["id"] if tecnicas else "T1046",
            },
            "enum": {
                "acao": "vuln_analysis",
                "descricao": "Analisar serviços para vulnerabilidades conhecidas",
                "ferramenta": "searchsploit + NIM analysis",
                "mitre": tecnicas[0]["id"] if tecnicas else "T1087",
            },
            "exploit": {
                "acao": "poc_generation",
                "descricao": "Gerar PoC para vulnerabilidade de maior severidade",
                "ferramenta": "ShadowForge PoC Engine",
                "mitre": tecnicas[0]["id"] if tecnicas else "T1190",
            },
            "post": {
                "acao": "privesc_analysis",
                "descricao": "Analisar vetores de privilege escalation",
                "ferramenta": "linpeas/winpeas",
                "mitre": tecnicas[0]["id"] if tecnicas else "T1068",
            },
            "report": {
                "acao": "generate_report",
                "descricao": "Gerar relatório profissional com recomendações",
                "ferramenta": "ReportGenerator",
                "mitre": "",
            },
        }

        return sugestoes.get(fase, sugestoes["recon"])

    def _buscar_em_memoria(self, query: str, fase: str = "", top_k: int = 5) -> list[dict[str, Any]]:
        """Busca in-memory (fallback quando ChromaDB indisponível)."""
        query_lower = query.lower()
        results = []

        for t in self.MITRE_TECNICAS:
            score = 0.0
            # Score por keyword match
            for kw in t["keywords"]:
                if kw in query_lower:
                    score += 0.3
            # Score por fase
            if fase and t["fase_sh4d0w"] == fase:
                score += 0.4
            # Score por nome
            if any(word in t["nome"].lower() for word in query_lower.split()):
                score += 0.2

            if score > 0:
                results.append({
                    "id": t["id"],
                    "descricao": f"{t['nome']}: {t['descricao']}",
                    "tatica": t["tatica"],
                    "fase": t["fase_sh4d0w"],
                    "score": min(score, 1.0),
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
