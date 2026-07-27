# Script simples para enviar alteracoes ao GitHub
Set-Location "C:\Users\Thinkin pad 8g\ShadowForge-Agent-review"

Write-Host "Adicionando arquivos..."
git add -A

Write-Host "Committing..."
git commit -m "Security hardening: 14 vulnerabilities fixed"

Write-Host "Configurando remote HTTPS..."
git remote set-url origin https://github.com/Lelolima/ShadowForge-Agent.git

Write-Host "Enviando para GitHub..."
git push -u origin main

Write-Host "`nConcluido!"