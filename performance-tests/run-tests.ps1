# Configurações gerais
$Repetitions = 10
$FlagDir = "results/flags"

# Cria pasta de flags se não existir
if (-not (Test-Path $FlagDir)) {
    New-Item -ItemType Directory -Path $FlagDir | Out-Null
}

# Função para executar um cenário simples
function Invoke-Scenario {
    param(
        [string]$ScenarioName,
        [int]$Users,
        [string]$Duration,
        [int]$Rep
    )

    $outputDir = "results\${ScenarioName}\rep${Rep}"
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    
    Write-Host "Executando $ScenarioName - Repetição $Rep" -ForegroundColor Cyan
    $HostUrl = "http://localhost:8080"  # Altere se necessário
    & locust -f locustfile.py --host=$HostUrl --users=$Users --spawn-rate=10 --run-time=$Duration --headless --csv="$outputDir\results"
}

# Função de rollback com checagem de saúde dos containers essenciais
function Rollback-Containers {
    param(
        [string[]]$EssentialContainers = @(
            "api-gateway",
            "customers-service",
            "visits-service"
        )
    )

    Write-Host "=== Rollback: Reiniciando containers ===" -ForegroundColor Yellow
    $composeFile = "C:\projetos\kaua\Trabalho_7_SD\spring-petclinic-microservices\docker-compose.yml"

    docker-compose -f $composeFile down -v
    docker-compose -f $composeFile up -d

    # Aguarda containers essenciais ficarem 'healthy'
    $timeout = 180  # segundos
    $interval = 5
    $elapsed = 0
    $hostUrl = "http://localhost:8080/api/customer/owners"  # health check
    $healthy = $false

    do {
        Start-Sleep -Seconds $interval
        $elapsed += $interval

        try {
            $response = Invoke-WebRequest -Uri $hostUrl -UseBasicParsing -TimeoutSec 3
            $healthy = ($response.StatusCode -eq 200)
        } catch {
            $healthy = $false
        }

    } while (-not $healthy -and $elapsed -lt $timeout)

    if ($healthy) {
        Write-Host "Serviço acessível e saudável." -ForegroundColor Green
    } else {
        Write-Warning "Timeout atingido, serviço pode não estar pronto."
    }
}

# Função para executar cenário com retry e rollback
function Invoke-Scenario-WithRollback {
    param(
        [string]$ScenarioName,
        [int]$Users,
        [string]$Duration,
        [int]$Rep
    )

    $maxRetries = 2
    $attempt = 0
    $success = $false

    while (-not $success -and $attempt -lt $maxRetries) {
        try {
            Rollback-Containers
            Invoke-Scenario -ScenarioName $ScenarioName -Users $Users -Duration $Duration -Rep $Rep
            $success = $true
        } catch {
            Write-Warning ("Erro ao executar {0} Repetição {1}: {2}" -f $ScenarioName, $Rep, $_)
            $attempt++
            if ($attempt -ge $maxRetries) {
                Write-Error ("Falha persistente no cenário {0} repetição {1}. Pulando." -f $ScenarioName, $Rep)
            } else {
                Write-Host ("Tentando novamente ({0}/{1})..." -f $attempt, $maxRetries) -ForegroundColor Cyan
            }
        }
    }
}

# Função para executar cenário com flags de finalização
function Execute-Scenario-WithFlag {
    param(
        [string]$ScenarioName,
        [int]$Users,
        [string]$Duration
    )

    for ($rep = 1; $rep -le $Repetitions; $rep++) {
        $flagFile = Join-Path $FlagDir "${ScenarioName}_rep${rep}_finalizado.flag"

        if (Test-Path $flagFile) {
            Write-Host "=== ${ScenarioName} Repetição $rep já finalizada. Pulando..." -ForegroundColor Yellow
            continue
        }

        Write-Host "=== ROUND $rep de $Repetitions - $ScenarioName ===" -ForegroundColor Magenta
        Invoke-Scenario-WithRollback -ScenarioName $ScenarioName -Users $Users -Duration $Duration -Rep $rep
        New-Item -ItemType File -Path $flagFile -Force | Out-Null
        Write-Host "Flag criada: $flagFile" -ForegroundColor Green
    }
}

# Execução dos cenários
Execute-Scenario-WithFlag -ScenarioName "CenarioA" -Users 50 -Duration "10m"
Execute-Scenario-WithFlag -ScenarioName "CenarioB" -Users 100 -Duration "10m"
Execute-Scenario-WithFlag -ScenarioName "CenarioC" -Users 200 -Duration "5m"
Execute-Scenario-WithFlag -ScenarioName "CenarioD" -Users 400 -Duration "5m"
