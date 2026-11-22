# 03 — Revisão de configuração insegura

**Problema.** Uma configuração do agente com guardrails desligados, escopo amplo demais ou
segredo colado no arquivo é perigosa. Ela precisa ser barrada antes do uso, de preferência
no CI.

**O que o exemplo faz.** Revisa `dados/config_insegura.yaml`, que é insegura de propósito e
usa um valor de chave fictício. Aponta:
- guardrails desativados;
- registro de ações desligado;
- escopo `10.0.0.0/8`, amplo demais;
- `0.0.0.0/0` na blacklist, o que bloqueia todo IPv4;
- ausência de loopback e metadata de nuvem na blacklist;
- `verify_ssl: false`;
- segredo em texto claro.

O valor do segredo **nunca** é impresso, só a chave onde ele está.

A mesma revisão existe na CLI: `python main.py --check-config --config <arquivo>`
(código de saída 1 se houver achado crítico ou alto).

**Como rodar.**
```bash
python examples/03_revisao_config/revisar.py
python examples/03_revisao_config/revisar.py --config config/default.yaml --falhar-se-grave
```

**Saída esperada (resumo).**
```
Revisão de config_insegura.yaml: 8 achado(s)
[CRITICAL] etica.exigir_autorizacao: Verificação de autorização desativada
[CRITICAL] nvidia.api_key: Segredo gravado em texto claro no arquivo de configuração
[HIGH    ] etica.whitelist_hosts: Escopo amplo demais: 10.0.0.0/8 (16777216 endereços)
...
```
