# Política de Segurança

## Versões Suportadas

| Versão | Suportada          | Correções de Segurança | Correções de Bugs  |
| ------- | ------------------ | -------------- | ---------- |
| 1.0.x   | :white_check_mark: | Sim            | Sim        |
| < 1.0   | :x:                | Não            | Não        |

## Relatando uma Vulnerabilidade

Levamos as vulnerabilidades de segurança a sério. Se você descobrir uma vulnerabilidade de segurança no ShadowForge, por favor, relate-a de forma responsável.

**NÃO** abra uma issue pública no GitHub para vulnerabilidades de segurança.

### Processo de Relato

1. **E-mail**: Envie um relatório detalhado para lelolima806@gmail.com
2. **GitHub**: Use o recurso [Consultoria de Segurança Privada](../../security/advisories/new)
3. **PGP**: Para relatórios sensíveis, criptografe com nossa chave PGP pública (disponível na raiz do repositório)

### O que Incluir

- **Descrição**: Descrição clara da vulnerabilidade
- **Impacto**: O que um atacante poderia alcançar (use CVSS v3.1 se possível)
- **Reprodução**: Instruções passo a passo para reproduzir
- **Prova de Conceito**: Código mínimo ou comandos demonstrando o problema
- **Versões Afetadas**: Qual(is) versão(ões) são afetadas
- **Correção Sugerida**: Se você tiver uma proposta de remediação

### Cronograma de Resposta

| Etapa | Tempo Alvo |
|-------|-------------|
| Confirmação | 48 horas |
| Avaliação Inicial | 5 dias úteis |
| Resposta Detalhada | 7 dias úteis |
| Desenvolvimento da Correção | 30 dias (crítico), 90 dias (outros) |
| Atribuição de CVE | Se aplicável, coordenado com o relator |

### Política de Divulgação

Seguimos a **divulgação responsável coordenada**:

- Os relatórios são mantidos confidenciais até que uma correção seja lançada
- Solicitamos um período de embargo de 90 dias antes da divulgação pública
- Os relatadores são creditados (a menos que prefiram permanecer anônimos)
- Não tomaremos medidas legais contra pesquisas de segurança feitas de boa fé

## Recursos de Segurança

Este projeto inclui várias camadas de segurança:

### Guarda-eti dens Éticos

- **Verificação de Autorização**: Requer confirmação explícita antes de qualquer teste de penetração
- **Lista Negra/Branca**: Restrições configuráveis de IP/hospedeiro para impedir direcionamento não autorizado
- **Prevenção de Ação Destrutiva**: Não pode excluir, destruir ou limpar dados do alvo
- **Prevenção de Portas dos Fundos**: Não pode instalar portas dos fundos persistentes nos alvos
- **Prevenção de Exfiltração**: Não pode exfiltrar dados reais dos alvos
- **Modo de Simulação**: Testes de ponta a ponta completos sem executar ataques reais

### Auditoria & Logging

- **Trilha de Auditoria Completa**: Cada ação do agente é registrada com timestamps
- **Sanitização de Logs**: Dados sensíveis (chaves de API, credenciais) são redigidos dos logs
- **Detecção de Adulteração**: Verificação de integridade de logs para responsabilidade forense

### Proteção de Dados

- **Local-First**: Todos os dados armazenados localmente (SQLite, ChromaDB)
- **Nenhum Armazenamento em Nuvem**: Resultados de scan, credenciais e relatórios nunca deixam o host
- **Isolamento de Ambiente**: Chaves de API carregadas apenas do `.env` (nunca hardcodeadas)
- **Exclusão do Git**: `.env`, `*.pem`, `*.key`, credenciais são ignoradas pelo git

### Cadeia de Suprimentos

- **Dependências Fixadas**: Todos os requisitos especificam versões mínimas
- **Varredura de Segurança**: Bandit integrado em CI e ganchos pré-commit
- **Detecção de Chave Privada**: Gancho pré-commit impede vazamentos acidentais de credenciais
- **Auditoria de Dependências**: Verificação `safety` no pipeline de CI

## Conformidade LGPD & GDPR

Este projeto é projetado com princípios de privacidade por projeto e privacidade por padrão:

### LGPD (Lei Geral de Proteção de Dados - Brasil)

- **Art. 4**: Dados pessoais processados apenas com base legal (consentimento de teste autorizado)
- **Art. 6**: Limitação de finalidade, adequação e minimização aplicadas por design
- **Art. 7**: Base legal é consentimento explícito do titular dos dados ou interesse legítimo
- **Art. 46**: Transferências internacionais de dados (API NVIDIA) cumprem requisitos de adequação
- **Art. 43**: Avaliação de Impacto à Proteção de Dados recomendada antes de campanhas

### GDPR (Regulamento Geral de Proteção de Dados - UE)

- **Art. 5**: Princípios de processamento -- lawfulness, limitação de finalidade, minimização de dados
- **Art. 6**: Base legal para processamento (consentimento explícito ou interesse legítimo)
- **Art. 25**: Proteção de dados por design e por padrão
- **Art. 32**: Segurança do processamento -- criptografia, resiliência, controles de acesso
- **Art. 35**: Avaliação de Impacto à Proteção de Dados recomendada para campanhas em larga escala
- **Art. 44-49**: Transferências internacionais de dados cumprem decisões de adequação

## Conformidade Legal

Este projeto é projetado para cumprir com:

- **LGPD** (Lei Geral de Proteção de Dados - Brasil)
- **GDPR** (Regulamento Geral de Proteção de Dados - UE)
- **CFAA** (Lei de Fraude e Abuso de Computador - EUA)
- **Convenção de Budapeste** (Convenção sobre Crime Cibernético)
- **LGPD** (Lei Geral de Proteção de Dados - Lei 13.709/2018)

Os usuários devem garantir que tenham autorização escrita adequada antes de usar esta ferramenta contra qualquer alvo. Acesso não autorizado a sistemas de computador é ilegal na maioria das jurisdições.

## Melhores Práticas de Segurança para Usuários

1. **Sempre use o modo de simulação primeiro** (`--simulate` flag)
2. **Nunca teste sistemas sem autorização escrita**
3. **Mantenha as chaves de API seguras** -- nunca faça commit do `.env` no controle de versão
4. **Revise os resultados do scan** antes de compartilhar -- redija qualquer PII
5. **Use VPN/proxy** para mascarar sua origem durante os testes
6. **Siga os limites de escopo** -- não exceda o escopo de teste autorizado
7. **Relate vulnerabilidades** encontradas durante os testes através dos canais adequados
8. **Destrua os dados locais** após a conclusão da campanha (`rm -rf data/ campaigns/`)