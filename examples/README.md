# Exemplos de uso em casos reais

Cada exemplo é um cenário completo e executável de **uso autorizado**. Eles usam só
dados gravados (sintéticos e versionados em `dados/`) ou um laboratório local que o
próprio exemplo cria em `127.0.0.1`. **Nenhum exemplo contata hosts externos.** Todos
rodam no CI pelo teste `tests/examples/test_exemplos.py`.

| # | Cenário | Comando |
|---|---------|---------|
| 01 | [Triagem de resultados de scanner existentes (XML do Nmap)](01_triagem_nmap/) | `python examples/01_triagem_nmap/triagem.py` |
| 02 | [Relatório de pentest a partir de achados registrados](02_relatorio_achados/) | `python examples/02_relatorio_achados/gerar_relatorio.py` |
| 03 | [Revisão de configuração insegura](03_revisao_config/) | `python examples/03_revisao_config/revisar.py` |
| 04 | [Reconhecimento web e relatório de laboratório local](04_lab_web_local/) | `python examples/04_lab_web_local/lab_web.py --yes` |

Pré-requisito: `pip install -r requirements.txt` na raiz do repositório.
Os scripts gravam a saída em `saida/<exemplo>/` (ignorado pelo git) ou no diretório passado em `--saida`.
