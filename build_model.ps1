Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INICIANDO COMPILACIÓN NEURONAL: ALETHEIA CORE" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Construyendo modelo personalizado en Ollama..."

# Ejecutar el build de ollama
ollama create aletheia-core -f Modelfile

if ($LASTEXITCODE -eq 0) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " [ÉXITO] El modelo 'aletheia-core' ha sido inyectado en Ollama." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host " [ERROR] Fallo en la inyección de Ollama." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
}
