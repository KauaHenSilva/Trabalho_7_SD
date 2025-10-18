# Script PowerShell para executar testes de performance do Spring PetClinic
# 
# Este script executa os três cenários de teste conforme especificado:
# - Cenário A: 50 usuários por 10 min
# - Cenário B: 100 usuários por 10 min  
# - Cenário C: 200 usuários por 5 min

param(
    [string]$HostUrl = "http://localhost:8080",
    [int]$Repetitions = 8
)

Write-Host "=== Teste de Performance Spring PetClinic ===" -ForegroundColor Green
Write-Host "Host: $HostUrl" -ForegroundColor Yellow
Write-Host "Repetições por cenário: $Repetitions" -ForegroundColor Yellow
Write-Host ""

# Função para executar um cenário
function Invoke-Scenario {
    param(
        [string]$ScenarioName,
        [int]$Users,
        [string]$Duration,
        [int]$Rep
    )
    
    $outputDir = "results\${ScenarioName}\rep${Rep}"
    
    Write-Host "Executando $ScenarioName - Repetição $Rep/$Repetitions" -ForegroundColor Cyan
    Write-Host "Usuários: $Users | Duração: $Duration" -ForegroundColor White
    
    # Criar diretório de resultados
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    
    # Executar Locust
    & locust -f locustfile.py --host=$HostUrl --users=$Users --spawn-rate=10 --run-time=$Duration --headless --csv="$outputDir\results"
    
    Write-Host "Resultados salvos em: $outputDir" -ForegroundColor Green
    Write-Host ""
}

# Verificar se Locust está instalado
try {
    & locust --version | Out-Null
} catch {
    Write-Error "Locust não encontrado. Instale com: pip install locust"
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

# Criar diretório de resultados principal
New-Item -ItemType Directory -Path "results" -Force | Out-Null

Write-Host "Iniciando testes de performance..." -ForegroundColor Green
Write-Host ""

# Executar todos os cenários
for ($rep = 1; $rep -le $Repetitions; $rep++) {
    Write-Host "=== ROUND $rep de $Repetitions ===" -ForegroundColor Magenta
    
    # Cenário A: 50 usuários por 10 min
    Invoke-Scenario -ScenarioName "CenarioA" -Users 50 -Duration "10m" -Rep $rep
    
    # Pausa entre cenários
    Start-Sleep -Seconds 30
    
    # Cenário B: 100 usuários por 10 min
    Invoke-Scenario -ScenarioName "CenarioB" -Users 100 -Duration "10m" -Rep $rep
    
    # Pausa entre cenários
    Start-Sleep -Seconds 30
    
    # Cenário C: 200 usuários por 5 min
    Invoke-Scenario -ScenarioName "CenarioC" -Users 200 -Duration "5m" -Rep $rep
    
    # Pausa maior entre rounds
    if ($rep -lt $Repetitions) {
        Write-Host "Pausa de 2 minutos antes do próximo round..." -ForegroundColor Yellow
        Start-Sleep -Seconds 120
    }
}

Write-Host "=== Testes Concluídos ===" -ForegroundColor Green
Write-Host "Todos os resultados foram salvos na pasta 'results'" -ForegroundColor Green