# 1. Gerar chave SSH
$keyPath = "$env:USERPROFILE\.ssh\ShadowForge-Agent"
if (-not (Test-Path $keyPath)) {
    ssh-keygen -t ed25519 -C "ShadowForge-Agent" -f $keyPath -N '""'
    Write-Host "Chave SSH gerada em $keyPath"
} else {
    Write-Host "Chave SSH ja existe em $keyPath"
}

# 2. Configurar SSH config
$sshConfig = "$env:USERPROFILE\.ssh\config"
$configEntry = @"
Host github-shadowforge
    HostName github.com
    User git
    IdentityFile $keyPath
    IdentitiesOnly yes
"@
if (-not (Select-String -Path $sshConfig -Pattern "github-shadowforge" -Quiet -ErrorAction SilentlyContinue)) {
    Add-Content -Path $sshConfig -Value $configEntry
    Write-Host "SSH config atualizado"
} else {
    Write-Host "SSH config ja contem entrada"
}

# 3. Mostrar chave publica para adicionar ao GitHub
Write-Host "`n=== COPIE ESTA CHAVE PUBLICA PARA O GITHUB ==="
Get-Content "$keyPath.pub"
Write-Host "=== FIM DA CHAVE ==="
Write-Host "`nAdicione em: https://github.com/Lelolima/ShadowForge-Agent/settings/keys"

# 4. Entrar no projeto
Set-Location "C:\Users\Thinkin pad 8g\ShadowForge-Agent-review"

# 5. Stage + commit
git add -A
git commit -m "Security hardening: fix 14 vulnerabilities across 13 files

- C-04: Whitelist command prefixes in pivot.py privesc checks
- C-05: Fix MAC spoof (6 octets, secrets.randbelow) + session ID (secrets.token_hex)
- C-06: MSF RPC SSL default True, localhost-only exception
- H-10: Plugin hash verification (SHA256) + security warning
- H-11: Dangerous command blacklist in StealthShell
- H-12: WebSocket auth token for dashboard
- H-13: Syslog truncation guardrail (impedir_destruicao)
- H-14: Regex JSON extraction in multimodal.py
- M-15: Block aggressive sqlmap/hydra flags
- M-16: Private IP ranges require explicit authorization
- M-17: Secure session ID generation (secrets.token_hex)
- M-18: URL scheme validation (http/https only) in web_attacks
- M-19: LRU cache limit for embeddings (max 500)
- M-20: Heap-based O(n) eviction in MemoriaCurtoPrazo
- Q-03: Call memoria_lp.close() on agent shutdown
- Q-08: Document TODO for subprocess_exec migration"

# 6. Configurar remote com SSH
git remote set-url origin git@github-shadowforge:Lelolima/ShadowForge-Agent.git

# 7. Push
git push -u origin main
