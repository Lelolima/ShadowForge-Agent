# Política de Privacidade

**Última atualização:** 2025-05-19
**Data de vigência:** 2025-05-19

---

## 1. Visão Geral

O ShadowForge é uma ferramenta de teste de segurança offline-first. Não coletamos **nenhum dado pessoal** por padrão. Esta política de privacidade descreve como os dados são tratados quando a ferramenta é usada para testes de penetração autorizados.

## 2. Controlador de Dados

O usuário (testador de penetração) é o controlador de dados. O projeto ShadowForge e seus colaboradores não coletam, processam ou têm acesso a nenhum dado gerado durante o uso. Todos os dados permanecem exclusivamente na máquina local do usuário.

## 3. Coleta de Dados

A ferramenta pode processar os seguintes dados **apenas durante testes de penetração autorizados**:

| Tipo de Dado | Finalidade | Armazenamento | Retenção |
|-------------|-----------|--------------|----------|
| IPs/Hosts alvo | Varredura de segurança | Local apenas | Duração da campanha |
| Resultados de scan | Análise de vulnerabilidades | SQLite local | 30 dias (configurável) |
| Capturas de tela | Análise visual | Sistema de arquivos local | Duração da campanha |
| Comandos de voz | Interface por voz | Não armazenado | Tempo real apenas |
| Estado da campanha | Persistência de sessão | SQLite local | Até exclusão manual |
| Prompts de IA | Inferência LLM | Não armazenado localmente | Enviado à API NVIDIA |

## 4. Processamento de Dados pela API NVIDIA

Ao usar inferência em nuvem NVIDIA NIM:

- Os prompts são enviados aos servidores da NVIDIA via conexão TLS criptografada
- Aplica-se a [Política de Privacidade da NVIDIA](https://www.nvidia.com/pt-br/about-nvidia/privacy-policy/) aos dados transmitidos
- Nenhum dado pessoal é incluído nos padrões de prompt
- Usuários devem evitar enviar dados pessoais (PII) para APIs em nuvem
- Os padrões podem incluir metadados do alvo (IPs, hostnames, versões de serviços) -- usuários devem avaliar se isso constitui dados pessoais sob a lei aplicável
- A NVIDIA pode reter padrões conforme sua política de retenção

## 5. Conformidade LGPD (Lei 13.709/2018)

Esta ferramenta está em conformidade com a LGPD:

- **Art. 4**: Dados pessoais são processados apenas com base legal (teste autorizado)
- **Art. 6**: O processamento segue finalidade, adequação e minimização
- **Art. 7**: A base legal é o consentimento ou interesse legítimo
- **Art. 8**: O consentimento pode ser revogado a qualquer momento
- **Art. 17**: Dados pessoais são excluídos após a conclusão da campanha
- **Art. 46**: Transferências internacionais (API NVIDIA) cumprem requisitos de adequação
- **Art. 48**: Solicitações do titular são tratadas localmente pelo controlador (usuário)

## 6. Conformidade GDPR (Regulamento 2016/679)

Esta ferramenta é projetada para cumprir o GDPR:

- **Art. 5**: Princípios -- legalidade, limitação de finalidade, minimização, exatidão, limitação de armazenamento, integridade/confidencialidade
- **Art. 6**: Base legal -- consentimento explícito ou interesse legítimo para testes de segurança
- **Art. 9**: Categorias especiais -- a ferramenta não é projetada para processar dados de categorias especiais
- **Art. 25**: Proteção de dados por design e por padrão (offline-first, armazenamento local, sem telemetria)
- **Art. 30**: Registros de processamento -- logs de campanha servem a este propósito
- **Art. 32**: Segurança do processamento -- criptografia, resiliência, controles de acesso
- **Art. 33-34**: Notificação de violação -- usuários são responsáveis por notificar os titulares afetados
- **Art. 35**: Avaliação de Impacto à Proteção de Dados (AIPD) recomendada para campanhas em larga escala
- **Art. 44-49**: Transferências internacionais -- transferências para API NVIDIA sujeitas a decisões de adequação ou CSCs

## 7. Direitos do Titular

Sob a LGPD (Arts. 18-19) e GDPR (Arts. 15-22), os titulares têm direito a:

- **Confirmação**: Confirmar a existência de tratamento de dados pessoais
- **Acesso**: Acessar dados pessoais mantidos pela ferramenta
- **Correção**: Corrigir dados incompletos, imprecisos ou desatualizados
- **Anonimização/Eliminação**: Eliminar dados desnecessários ou excessivos
- **Portabilidade**: Exportar dados em formato estruturado e de leitura automatizada
- **Revogação**: Revogar consentimento a qualquer momento
- **Oposição**: Opor-se ao processamento baseado em interesse legítimo

Para exercer esses direitos: basta excluir o diretório local `data/` ou usar o recurso de limpeza de campanha. Entre em contato com o controlador de dados (usuário/organização executando o teste) para solicitações de titulares.

## 8. Retenção de Dados

| Tipo de Dado | Retenção Padrão | Método de Limpeza |
|-------------|----------------|-------------------|
| Dados de campanha | 30 dias | Limpeza automática via config |
| Resultados de scan | Duração da campanha | Manual: `rm -rf data/` |
| Logs | 30 dias | Rotação de logs (configurável) |
| Prompts de IA | Não retidos localmente | N/A (enviado à API NVIDIA) |

## 9. Serviços de Terceiros

| Serviço | Finalidade | Dados Compartilhados | Política de Privacidade |
|---------|-----------|---------------------|------------------------|
| NVIDIA NIM API | Inferência LLM | Padrões (sem PII por padrão) | [Privacidade NVIDIA](https://www.nvidia.com/pt-br/about-nvidia/privacy-policy/) |
| NVIDIA Riva | ASR/TTS | Áudio de voz (local ou on-premise) | Disponível para implantação on-premise |
| Shodan API | OSINT | Consultas IP/hostname | [Privacidade Shodan](https://shodan.io/privacy) |
| Censys API | OSINT | Consultas IP/hostname | [Privacidade Censys](https://censys.io/privacy) |

## 10. Contato

Para questões relacionadas à privacidade, contate os mantenedores do projeto via GitHub Issues ou e-mail security@shadowforge.dev.