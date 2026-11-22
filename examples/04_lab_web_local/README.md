# 04 — Reconhecimento web e relatório de laboratório local

**Problema.** É preciso verificar a configuração de segurança HTTP de uma aplicação de
homologação e documentar o resultado, sem tocar nada fora do autorizado e deixando
registro de quem fez o quê.

**O que o exemplo faz.**
1. Sobe um servidor HTTP de laboratório em `127.0.0.1`, numa porta aleatória, com
   cabeçalhos propositalmente fracos.
2. Define o escopo autorizado como **apenas** `127.0.0.1` e verifica os guardrails.
3. Pede **confirmação** antes de enviar a requisição. `--yes` confirma; sem terminal e sem
   `--yes`, nega e sai com código 3, sem tocar o alvo.
4. Faz o fingerprint web com o `ReconScanner` e revisa os cabeçalhos: CSP,
   X-Frame-Options, nosniff, Referrer-Policy, banner com versão e cookie sem
   HttpOnly/SameSite.
5. Gera o relatório e a trilha de auditoria JSONL encadeada por hash, e confere sua integridade.

O laboratório é encerrado ao fim. Nenhum outro host é contatado.

**Como rodar.**
```bash
python examples/04_lab_web_local/lab_web.py --yes
```

**Saída esperada (resumo).**
```
Guardrails: PERMITIDO (Ação permitida pelos guardrails éticos)
HTTP 200 em http://127.0.0.1:<porta>/
[MEDIUM] Cabeçalho Content-Security-Policy ausente -> Definir uma CSP restritiva ...
[LOW   ] Server expõe versão de software (Apache/2.4.41 (Ubuntu)) -> ...
[MEDIUM] Cookie sem atributos: httponly, samesite -> ...
Trilha de auditoria: saida/04_lab_web_local/audit/SF-....jsonl (5 eventos, íntegra=True)
```
