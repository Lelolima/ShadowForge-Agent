# Registro de Alterações

Todas as alterações significativas deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
e este projeto aderisce ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-06-03

### Corrigido
- Typo crítico: `MemoriLongoPrazo` → `MemoriaLongoPrazo` (classe inacessível)
- Typo crítico: dependência com espaço `" Reconhecimento Passivo"` no orchestrator quebrava resolução
- Vazamentos de conexão SQLite: `_init_db`, `_salvar_vulnerabilidade_db`, `_salvar_acao_db`, `_atualizar_fase_db` agora usam context managers
- EventBus `stop()` agora faz flush dos eventos pendentes antes de parar
- Lógica IDOR: avaliação agora é feita após coletar TODAS as respostas (antes avaliava a cada iteração)
- `shlex.quote` no Windows: substituído por `_safe_quote()` com escaping adequado para CMD/PowerShell
- Typo: `estatisicas()` → `estatisticas()` em MemoriaLongoPrazo
- Typo: `log_retenciao_dias` → `log_retencao_dias` em ShadowForgeConfig

### Alterado
- Decisores OODA (`_decidir_scan`, `_decidir_enum`, `_decidir_post`) agora utilizam dados de orientação/RAG
- `_decidir_exploit` agora prioriza vulnerabilidades por severidade (critical → high → medium → low)
- `_decidir_recon` inclui contagem de técnicas RAG na decisão

## [1.0.0] - 2025-05-19

### Adicionado
- OODA Loop (Observe-Orient-Decide-Act) motor de agente autônomo
- Integração NVIDIA NIM com fallback multi-modelo (Llama 3.3 70B, Llama 3.2 Vision)
- Suporte à interface de voz NVIDIA Riva ASR/TTS
- Máquina de estado Kill Chain: IDLE -> RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT
- Sistema de configuração Pydantic v2 com suporte a YAML + variáveis de ambiente
- Guardrails éticos com blacklist/whitelist, verificação de autorização
- Subsistema de Visão: captura de tela, OCR (Tesseract), detecção YOLOv8
- Controle furtivo: mouse (curvas de Bézier), teclado (atrasos semelhantes aos humanos), shell
- Planejamento RAG com bases de conhecimento MITRE ATT&CK e OWASP (ChromaDB)
- Módulo de reconhecimento OSINT
- Orquestrador de campanha com auto-salve e histórico
- 4 demonstrações de exemplo: laboratório de pentest, bounty de bugs, controle DOOM, campanha por voz
- Suporte a Docker com Dockerfile e docker-compose.yaml
- Suíte profissional de testes: validação de importação, testes de conectividade de API
- Scripts de verificação de saúde e validação de ambiente
- Modo de simulação para testes seguros sem ataques reais

### Segurança
- Arquivos .env excluídos do controle de versão
- Chaves de API carregadas apenas de variáveis de ambiente
- Guardrails éticos que impedem ações destrutivas
- Registro de trilha de auditoria para todas as operações
- Verificação de autorização antes da execução da campanha

### Alterado
- Cliente NIM: degradação graciosa quando a chave de API não está disponível
- Cliente NIM: descoberta automática e fallback de modelo
- Config: corrigida a URL base da NVIDIA para incluir o caminho /v1/
- Blacklist: removido o intervalo excessivamente amplo 0.0.0.0/0 que bloqueava todos os alvos

### Corrigido
- Problemas de codificação UTF-8 no Windows (cp1252 -> utf-8)
- Erros de indentação YAML em default.yaml
- IndentationError no módulo OSINT
- Agente preso na fase de scan (manipuladores de ação ausentes)
- Aviso de sessão aiohttp não fechada no desligamento

[1.0.0]: https://github.com/shadowforge/NVIDIA-ShadowForge-Agent/releases/tag/v1.0.0
