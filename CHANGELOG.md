# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-19

### Added
- OODA Loop (Observe-Orient-Decide-Act) autonomous agent engine
- NVIDIA NIM integration with multi-model fallback (Llama 3.3 70B, Llama 3.2 Vision)
- NVIDIA Riva ASR/TTS voice interface support
- Kill Chain state machine: IDLE -> RECON -> SCAN -> ENUM -> EXPLOIT -> POST -> REPORT
- Pydantic v2 configuration system with YAML + env var support
- Ethical guardrails with blacklist/whitelist, authorization verification
- Vision subsystem: screen capture, OCR (Tesseract), YOLOv8 detection
- Stealth control: mouse (Bezier curves), keyboard (human-like delays), shell
- RAG planning with MITRE ATT&CK and OWASP knowledge bases (ChromaDB)
- OSINT reconnaissance module
- Campaign orchestrator with auto-save and history
- 4 example demos: pentest lab, bug bounty, DOOM control, voice campaign
- Docker support with Dockerfile and docker-compose.yaml
- Professional test suite: import validation, API connectivity tests
- Health check and environment validation scripts
- Simulation mode for safe testing without real attacks

### Security
- .env files excluded from version control
- API keys loaded from environment variables only
- Ethical guardrails preventing destructive actions
- Audit trail logging for all operations
- Authorization verification before campaign execution

### Changed
- NIM Client: graceful degradation when API key unavailable
- NIM Client: automatic model discovery and fallback
- Config: corrected NVIDIA base URL to include /v1/ path
- Blacklist: removed overly broad 0.0.0.0/0 that blocked all targets

### Fixed
- Windows UTF-8 encoding issues (cp1252 -> utf-8)
- YAML indentation errors in default.yaml
- IndentationError in OSINT module
- Agent stuck in scan phase (missing action handlers)
- Unclosed aiohttp session warning on shutdown

[1.0.0]: https://github.com/shadowforge/NVIDIA-ShadowForge-Agent/releases/tag/v1.0.0
