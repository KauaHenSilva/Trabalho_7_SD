# Script de teste rápido para demonstração
# Execute testes de performance reduzidos para validar a configuração

param(
    [string]$HostUrl = "http://localhost:8080"
)

Write-Host "=== Teste de Performance DEMO - Spring PetClinic ===" -ForegroundColor Green
Write-Host "Host: $HostUrl" -ForegroundColor Yellow
Write-Host ""

# Verificar se Locust está disponível
try {
    & locust --version | Out-Null
    Write-Host "Locust encontrado!" -ForegroundColor Green
} catch {
    Write-Error "Locust não encontrado. Execute: pip install locust"
    exit 1
}

# Verificar se o host está respondendo
try {
    $response = Invoke-WebRequest -Uri "$HostUrl/api/customer/owners" -Method GET -TimeoutSec 10
    if ($response.StatusCode -ne 200) {
        throw "Status code: $($response.StatusCode)"
    }
    Write-Host "Aplicação PetClinic respondendo corretamente" -ForegroundColor Green
} catch {
    Write-Error "Aplicação PetClinic não está respondendo em $HostUrl"
    Write-Error "Certifique-se de que a aplicação está rodando com docker-compose up"
    exit 1
}

# Criar diretório para resultados
New-Item -ItemType Directory -Path "demo_results" -Force | Out-Null

Write-Host "Executando testes demo (versão reduzida)..." -ForegroundColor Green
Write-Host ""

# Teste Demo A: 10 usuários por 1 minuto
Write-Host "Demo A: 10 usuários por 1 minuto" -ForegroundColor Cyan
& locust -f locustfile.py --host=$HostUrl --users=10 --spawn-rate=2 --run-time=1m --headless --csv="demo_results/demo_a"

Start-Sleep -Seconds 10

# Teste Demo B: 25 usuários por 1 minuto
Write-Host "Demo B: 25 usuários por 1 minuto" -ForegroundColor Cyan
& locust -f locustfile.py --host=$HostUrl --users=25 --spawn-rate=5 --run-time=1m --headless --csv="demo_results/demo_b"

Start-Sleep -Seconds 10

# Teste Demo C: 50 usuários por 1 minuto
Write-Host "Demo C: 50 usuários por 1 minuto" -ForegroundColor Cyan
& locust -f locustfile.py --host=$HostUrl --users=50 --spawn-rate=10 --run-time=1m --headless --csv="demo_results/demo_c"

Write-Host ""
Write-Host "=== Testes Demo Concluídos ===" -ForegroundColor Green
Write-Host "Resultados salvos na pasta 'demo_results'" -ForegroundColor Green
Write-Host ""
Write-Host "Para análise dos resultados:" -ForegroundColor Yellow
Write-Host "python analyze_results.py" -ForegroundColor White
Write-Host ""
Write-Host "Para executar os testes completos (30 repetições cada):" -ForegroundColor Yellow
Write-Host ".\run-tests.ps1" -ForegroundColor White