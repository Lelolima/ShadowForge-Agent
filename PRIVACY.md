# Privacy Policy / Politica de Privacidade

**Last updated / Ultima atualizacao:** 2025-05-19
**Effective date / Data de vigencia:** 2025-05-19

---

## English

### 1. Overview

ShadowForge is an offline-first security testing tool. We collect **NO personal
data** by default. This privacy policy describes how data is handled when the
tool is used for authorized penetration testing.

### 2. Data Controller

The user (penetration tester) is the data controller. The ShadowForge project
and its contributors do not collect, process, or have access to any data
generated during use. All data remains exclusively on the user's local machine.

### 3. Data Collection

The tool may process the following data **only during authorized penetration tests**:

| Data Type | Purpose | Storage | Retention |
|-----------|---------|---------|-----------|
| Target IPs/Hosts | Security scanning | Local only | Campaign duration |
| Scan results | Vulnerability analysis | Local SQLite | 30 days (configurable) |
| Screenshots | Visual analysis | Local filesystem | Campaign duration |
| Voice commands | Voice interface | Not stored | Real-time only |
| Campaign state | Session persistence | Local SQLite | Until manually deleted |
| AI prompts | LLM inference | Not stored locally | Sent to NVIDIA API |

### 4. NVIDIA API Data Processing

When using NVIDIA NIM cloud inference:

- Prompts are sent to NVIDIA's API servers over encrypted TLS connections
- NVIDIA's [Privacy Policy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) applies to data transmitted to their services
- No personal data is included in prompts by default
- Users should avoid sending PII (Personally Identifiable Information) to cloud APIs
- Prompts may include target metadata (IPs, hostnames, service versions) -- users should assess whether this constitutes personal data under applicable law
- NVIDIA may retain prompts per their data retention policy

### 5. LGPD Compliance (Lei Geral de Protecao de Dados - Brazil)

This tool complies with Brazilian LGPD (Law 13.709/2018):

- **Art. 4**: Personal data is only processed with legal basis (authorized testing)
- **Art. 6**: Data processing follows purpose limitation, adequacy, and minimization
- **Art. 7**: Legal basis is the data subject's consent or legitimate interest
- **Art. 8**: Consent may be revoked at any time
- **Art. 17**: Personal data is deleted after campaign completion
- **Art. 46**: International data transfers (NVIDIA API) comply with adequacy requirements
- **Art. 48**: Data subject requests are handled locally by the data controller (user)

### 6. GDPR Compliance (General Data Protection Regulation - EU)

This tool is designed to comply with GDPR (Regulation 2016/679):

- **Art. 5**: Principles -- lawfulness, purpose limitation, data minimization, accuracy, storage limitation, integrity/confidentiality
- **Art. 6**: Lawful basis -- explicit consent or legitimate interest for security testing
- **Art. 9**: Special categories -- the tool is not designed to process special category data
- **Art. 25**: Data protection by design and by default (offline-first, local storage, no telemetry)
- **Art. 30**: Records of processing -- campaign logs serve this purpose
- **Art. 32**: Security of processing -- encryption, access controls, audit trails
- **Art. 33-34**: Breach notification -- users are responsible for notifying affected data subjects
- **Art. 35**: Data Protection Impact Assessment (DPIA) recommended for large-scale campaigns
- **Art. 44-49**: International transfers -- NVIDIA API transfers subject to adequacy decisions or SCCs

### 7. User Rights

Under LGPD (Arts. 18-19) and GDPR (Arts. 15-22), data subjects have the right to:

- **Confirmation**: Confirm the existence of personal data processing
- **Access**: Access personal data held by the tool
- **Correction**: Correct incomplete, inaccurate, or outdated data
- **Anonymization/Deletion**: Delete unnecessary or excess data
- **Portability**: Export data in a structured, machine-readable format
- **Revocation**: Revoke consent at any time
- **Opposition**: Object to processing based on legitimate interest

To exercise these rights: simply delete the local `data/` directory or use the
campaign cleanup feature. Contact the data controller (the user/organization
running the test) for data subject requests.

### 8. Data Retention

| Data Type | Default Retention | Cleanup Method |
|-----------|-------------------|----------------|
| Campaign data | 30 days | Automatic cleanup via config |
| Scan results | Campaign duration | Manual: `rm -rf data/` |
| Logs | 30 days | Log rotation (configurable) |
| AI prompts | Not retained locally | N/A (sent to NVIDIA API) |

### 9. Third-Party Services

| Service | Purpose | Data Shared | Privacy Policy |
|---------|---------|-------------|----------------|
| NVIDIA NIM API | LLM inference | Prompts (no PII by default) | [NVIDIA Privacy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) |
| NVIDIA Riva | ASR/TTS | Voice audio (local or on-prem) | On-premise deployment available |
| Shodan API | OSINT | IP/hostname queries | [Shodan Privacy](https://shodan.io/privacy) |
| Censys API | OSINT | IP/hostname queries | [Censys Privacy](https://censys.io/privacy) |

### 10. Contact

For privacy-related questions, contact the project maintainers via GitHub Issues
or email security@shadowforge.dev.

---

## Portugues

### 1. Visao Geral

O ShadowForge e uma ferramenta de teste de seguranca offline-first. Nao coletamos
**nenhum dado pessoal** por padrao. Esta politica de privacidade descreve como os
dados sao tratados quando a ferramenta e usada para testes de penetracao autorizados.

### 2. Controlador de Dados

O usuario (testador de penetracao) e o controlador de dados. O projeto ShadowForge
e seus contribuidores nao coletam, processam ou tem acesso a qualquer dado gerado
durante o uso. Todos os dados permanecem exclusivamente na maquina local do usuario.

### 3. Coleta de Dados

A ferramenta pode processar os seguintes dados **apenas durante testes de
penetracao autorizados**:

| Tipo de Dado | Finalidade | Armazenamento | Retencao |
|-------------|-----------|--------------|----------|
| IPs/Hosts alvo | Varredura de seguranca | Local apenas | Duracao da campanha |
| Resultados de scan | Analise de vulnerabilidades | SQLite local | 30 dias (configuravel) |
| Capturas de tela | Analise visual | Sistema de arquivos local | Duracao da campanha |
| Comandos de voz | Interface por voz | Nao armazenado | Tempo real apenas |
| Estado da campanha | Persistencia de sessao | SQLite local | Ate exclusao manual |
| Prompts de IA | Inferencia LLM | Nao armazenado localmente | Enviado a API NVIDIA |

### 4. Processamento de Dados pela API NVIDIA

Ao usar inferencia cloud NVIDIA NIM:

- Prompts sao enviados aos servidores da NVIDIA via conexao TLS criptografada
- Aplica-se a [Politica de Privacidade da NVIDIA](https://www.nvidia.com/pt-br/about-nvidia/privacy-policy/) aos dados transmitidos
- Nenhum dado pessoal e incluido em prompts por padrao
- Usuarios devem evitar enviar dados pessoais (PII) para APIs cloud
- Prompts podem incluir metadados do alvo (IPs, hostnames, versoes de servicos) -- usuarios devem avaliar se isso constitui dados pessoais sob a lei aplicavel
- A NVIDIA pode reter prompts conforme sua politica de retencao

### 5. Conformidade LGPD (Lei 13.709/2018)

Esta ferramenta esta em conformidade com a LGPD:

- **Art. 4**: Dados pessoais sao processados apenas com base legal (teste autorizado)
- **Art. 6**: Processamento segue finalidade, adequacao e minimizacao
- **Art. 7**: Base legal e o consentimento ou interesse legitimo
- **Art. 8**: Consentimento pode ser revogado a qualquer momento
- **Art. 17**: Dados pessoais sao excluidos apos conclusao da campanha
- **Art. 46**: Transferencias internacionais (API NVIDIA) cumprem requisitos de adequacao
- **Art. 48**: Solicitacoes do titular sao tratadas localmente pelo controlador (usuario)

### 6. Conformidade GDPR (Regulamento 2016/679)

Esta ferramenta e projetada para cumprir o GDPR:

- **Art. 5**: Principios -- legalidade, limitacao de finalidade, minimizacao, exatidao, limitacao de armazenamento, integridade/confidencialidade
- **Art. 6**: Base legal -- consentimento explicito ou interesse legitimo para testes de seguranca
- **Art. 9**: Categorias especiais -- a ferramenta nao e projetada para processar dados de categorias especiais
- **Art. 25**: Protecao de dados por design e por padrao (offline-first, armazenamento local, sem telemetria)
- **Art. 30**: Registros de processamento -- logs de campanha servem a este proposito
- **Art. 32**: Seguranca do processamento -- criptografia, controles de acesso, trilhas de auditoria
- **Art. 33-34**: Notificacao de violacao -- usuarios sao responsaveis por notificar titulares afetados
- **Art. 35**: Avaliacao de Impacto a Protecao de Dados (RIPD) recomendada para campanhas em larga escala
- **Art. 44-49**: Transferencias internacionais -- transferencias para API NVIDIA sujeitas a decisoes de adequacao ou CCS

### 7. Direitos do Titular

Sob a LGPD (Arts. 18-19) e GDPR (Arts. 15-22), os titulares tem direito a:

- **Confirmacao**: Confirmar a existencia de tratamento de dados pessoais
- **Acesso**: Acessar dados pessoais mantidos pela ferramenta
- **Correcao**: Corrigir dados incompletos, imprecisos ou desatualizados
- **Anonimizacao/Eliminacao**: Eliminar dados desnecessarios ou excessivos
- **Portabilidade**: Exportar dados em formato estruturado e de leitura automatizada
- **Revogacao**: Revogar consentimento a qualquer momento
- **Oposicao**: Opor-se ao processamento baseado em interesse legitimo

Para exercer esses direitos: basta deletar o diretorio local `data/` ou usar
o recurso de limpeza de campanha. Contate o controlador de dados (usuario/organizacao
executando o teste) para solicitacoes de titulares.

### 8. Retencao de Dados

| Tipo de Dado | Retencao Padrao | Metodo de Limpeza |
|-------------|----------------|-------------------|
| Dados de campanha | 30 dias | Limpeza automatica via config |
| Resultados de scan | Duracao da campanha | Manual: `rm -rf data/` |
| Logs | 30 dias | Rotacao de logs (configuravel) |
| Prompts de IA | Nao retidos localmente | N/A (enviado a API NVIDIA) |

### 9. Servicos de Terceiros

| Servico | Finalidade | Dados Compartilhados | Politica de Privacidade |
|---------|-----------|---------------------|------------------------|
| NVIDIA NIM API | Inferencia LLM | Prompts (sem PII por padrao) | [Privacidade NVIDIA](https://www.nvidia.com/pt-br/about-nvidia/privacy-policy/) |
| NVIDIA Riva | ASR/TTS | Audio de voz (local ou on-premise) | Disponivel para implantacao on-premise |
| Shodan API | OSINT | Consultas IP/hostname | [Privacidade Shodan](https://shodan.io/privacy) |
| Censys API | OSINT | Consultas IP/hostname | [Privacidade Censys](https://censys.io/privacy) |

### 10. Contato

Para questoes relacionadas a privacidade, contate os mantenedores do projeto via
GitHub Issues ou email security@shadowforge.dev.
