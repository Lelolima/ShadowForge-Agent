# 01 — Triagem de resultados de scanner existentes

**Problema.** Depois de um scan autorizado, a equipe recebe um XML do Nmap com dezenas de
portas e precisa priorizar o que corrigir, sem incluir por engano hosts que estão fora
do contrato.

**O que o exemplo faz.**
1. Lê `dados/scan_lab.xml`, um scan **sintético** do laboratório fictício 10.10.10.0/24.
2. Descarta hosts fora do escopo de `dados/escopo.txt` (aqui, `10.10.20.7`).
3. Classifica as exposições: Telnet, bancos e caches acessíveis, FTP, SMB, RDP/VNC, HTTP sem TLS, OpenSSH e Apache desatualizados.
4. Grava `triagem.json` e um relatório em Markdown, JSON e HTML.

Nada é executado contra a rede.

**Como rodar.**
```bash
python examples/01_triagem_nmap/triagem.py
# com seus próprios dados:
python examples/01_triagem_nmap/triagem.py --xml scan.xml --escopo escopo.txt --saida saida/
```

**Saída esperada (resumo).**
```
Hosts ativos no XML: 4 | analisados (no escopo): 3
Ignorados por estarem FORA do escopo: 10.10.20.7
HIGH       10.10.10.12:3306   Banco de dados/cache acessível pela rede
HIGH       10.10.10.20:23     Telnet exposto (credenciais em texto claro)
MEDIUM     10.10.10.5:22      OpenSSH desatualizado (OpenSSH 7.4)
...
Resumo: {"critical": 0, "high": 3, "medium": 4, "low": 1, "info": 0}
```
