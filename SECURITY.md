# Security Policy

## Supported Versions

| Version | Supported          | Security Fixes | Bug Fixes  |
| ------- | ------------------ | -------------- | ---------- |
| 1.0.x   | :white_check_mark: | Yes            | Yes        |
| < 1.0   | :x:                | No             | No         |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security
vulnerability in ShadowForge, please report it responsibly.

**DO NOT** file a public GitHub issue for security vulnerabilities.

### Reporting Process

1. **Email**: Send a detailed report to lelolima806@gmail.com
2. **GitHub**: Use the [Private Security Advisory](../../security/advisories/new) feature
3. **PGP**: For sensitive reports, encrypt with our public PGP key (available in the repository root)

### What to Include

- **Description**: Clear description of the vulnerability
- **Impact**: What an attacker could achieve (use CVSS v3.1 if possible)
- **Reproduction**: Step-by-step instructions to reproduce
- **Proof of Concept**: Minimal code or commands demonstrating the issue
- **Affected Versions**: Which version(s) are affected
- **Suggested Fix**: If you have a proposed remediation

### Response Timeline

| Stage | Target Time |
|-------|-------------|
| Acknowledgment | 48 hours |
| Initial Assessment | 5 business days |
| Detailed Response | 7 business days |
| Fix Development | 30 days (critical), 90 days (others) |
| CVE Assignment | If applicable, coordinated with reporter |

### Disclosure Policy

We follow **coordinated responsible disclosure**:

- Reports are kept confidential until a fix is released
- We request a 90-day embargo period before public disclosure
- Reporters are credited (unless they prefer to remain anonymous)
- We will not take legal action against good-faith security research

## Security Features

This project includes multiple layers of security:

### Ethical Guardrails

- **Authorization Verification**: Requires explicit confirmation before any penetration test
- **Blacklist/Whitelist**: Configurable IP/host restrictions to prevent unauthorized targeting
- **Destructive Action Prevention**: Cannot delete, destroy, or wipe target data
- **Backdoor Prevention**: Cannot install persistent backdoors on targets
- **Exfiltration Prevention**: Cannot exfiltrate real data from targets
- **Simulation Mode**: Full end-to-end testing without executing real attacks

### Audit & Logging

- **Full Audit Trail**: Every agent action is logged with timestamps
- **Log Sanitization**: Sensitive data (API keys, credentials) are redacted from logs
- **Tamper Detection**: Log integrity verification for forensic accountability

### Data Protection

- **Local-First**: All data stored locally (SQLite, ChromaDB)
- **No Cloud Storage**: Scan results, credentials, and reports never leave the host
- **Environment Isolation**: API keys loaded from `.env` only (never hardcoded)
- **Git Exclusion**: `.env`, `*.pem`, `*.key`, credentials are gitignored

### Supply Chain

- **Pinned Dependencies**: All requirements specify minimum versions
- **Security Scanning**: Bandit integrated in CI and pre-commit hooks
- **Private Key Detection**: Pre-commit hook prevents accidental credential leaks
- **Dependency Audits**: `safety` check in CI pipeline

## LGPD & GDPR Compliance

This project is designed with privacy-by-design and privacy-by-default principles:

### LGPD (Lei Geral de Protecao de Dados - Brazil)

- **Art. 4**: Personal data processed only with legal basis (authorized testing consent)
- **Art. 6**: Purpose limitation, adequacy, and minimization enforced by design
- **Art. 7**: Legal basis is explicit consent from data subject or legitimate interest
- **Art. 46**: International data transfers (NVIDIA API) comply with adequacy requirements
- **Art. 43**: Data Protection Impact Assessment recommended before campaigns

### GDPR (General Data Protection Regulation - EU)

- **Art. 5**: Principles of processing -- lawfulness, purpose limitation, data minimization
- **Art. 6**: Lawful basis for processing (explicit consent or legitimate interest)
- **Art. 25**: Data protection by design and by default
- **Art. 32**: Security of processing -- encryption, resilience, access controls
- **Art. 35**: Data Protection Impact Assessment recommended for large-scale campaigns
- **Art. 44-49**: International data transfers comply with adequacy decisions

## Legal Compliance

This project is designed to comply with:

- **LGPD** (Lei Geral de Protecao de Dados - Brazil)
- **GDPR** (General Data Protection Regulation - EU)
- **CFAA** (Computer Fraud and Abuse Act - US)
- **Budapest Convention** (Convention on Cybercrime)
- **LGPD** (Lei Geral de Protecao de Dados - Lei 13.709/2018)

Users must ensure they have proper written authorization before using this tool
against any target. Unauthorized access to computer systems is illegal in most
jurisdictions.

## Security Best Practices for Users

1. **Always use simulation mode first** (`--simulate` flag)
2. **Never test systems without written authorization**
3. **Keep API keys secure** -- never commit `.env` to version control
4. **Review scan results** before sharing -- redact any PII
5. **Use VPN/proxy** to mask your origin during testing
6. **Follow scope boundaries** -- do not exceed authorized test scope
7. **Report vulnerabilities** found during testing through proper channels
8. **Destroy local data** after campaign completion (`rm -rf data/ campaigns/`)
