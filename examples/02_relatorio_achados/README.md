# 02 — Relatório de pentest a partir de achados registrados

**Problema.** Ao final de um teste autorizado, os achados estão anotados à mão (planilha
ou JSON) e é preciso entregar um relatório padronizado com resumo executivo, score,
recomendações e anexos.

**O que o exemplo faz.** Valida `dados/achados.json` (achados **fictícios** da aplicação
de laboratório `loja-lab.local`, que não existe) e gera o relatório em Markdown, JSON e
HTML com o `ReportGenerator` do projeto. Uma entrada inválida (tipo ou severidade
desconhecidos, campo obrigatório ausente) encerra com código 2 e uma mensagem clara.

**Como rodar.**
```bash
python examples/02_relatorio_achados/gerar_relatorio.py
python examples/02_relatorio_achados/gerar_relatorio.py --achados meus_achados.json --saida saida/
```
Valores aceitos em `tipo` e `severidade`: veja `TipoVulnerabilidade` e `Severidade` em `core/state.py`.

**Saída esperada.**
```
Campanha LAB-2026-01 | alvo loja-lab.local
Vulnerabilidades: 4 (críticas 1, altas 1) | risco CRÍTICO | score 7.8/10
Relatório markdown: saida/02_relatorio_achados/report_LAB-2026-01.md
```
