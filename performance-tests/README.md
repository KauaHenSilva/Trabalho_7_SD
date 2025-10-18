# Avaliação de Performance - Spring PetClinic Microservices

Este projeto contém testes automatizados de performance para o Spring PetClinic (versão microservices) usando Locust.

## Objetivo

Medir e relatar o desempenho básico do Spring PetClinic em três cenários de carga:
- **Cenário A**: 50 usuários por 10 minutos
- **Cenário B**: 100 usuários por 10 minutos  
- **Cenário C**: 200 usuários por 5 minutos

## Métricas Coletadas

- Tempo médio de resposta (ms)
- Tempo máximo de resposta (ms)
- Requisições por segundo (req/s)
- Total de requisições
- Taxa de sucesso (%)
- Número de erros

## Endpoints Testados

O script simula um mix realista de uso:
- `GET /api/customer/owners` (40% das requisições) - Lista proprietários
- `GET /api/customer/owners/{id}` (30% das requisições) - Detalhes do proprietário
- `GET /api/vet/vets` (20% das requisições) - Lista veterinários
- `POST /api/customer/owners` (10% das requisições) - Criar novo proprietário

## Estrutura dos Arquivos

```
performance-tests/
├── locustfile.py          # Script principal do Locust
├── run-tests.ps1          # Script PowerShell para executar todos os testes
├── analyze_results.py     # Script Python para análise dos resultados
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
└── results/              # Pasta onde são salvos os resultados
    └── analysis/         # Pasta onde são salvos gráficos e relatórios
```

## Pré-requisitos

### 1. Python e Dependências
```bash
pip install -r requirements.txt
```

### 2. Spring PetClinic Rodando
Certifique-se de que a aplicação está rodando em http://localhost:8080:
```bash
cd ../spring-petclinic-microservices
docker-compose up -d
```

Verifique se está funcionando:
```bash
curl http://localhost:8080/api/customer/owners
```

## Como Executar

### Opção 1: Script Automatizado (Recomendado)
Execute todos os 3 cenários com 30 repetições cada:
```powershell
.\run-tests.ps1
```

Ou customizar parâmetros:
```powershell
.\run-tests.ps1 -HostUrl "http://localhost:8080" -Repetitions 5
```

### Opção 2: Executar Cenários Individuais
```bash
# Cenário A: 50 usuários por 10 min
locust -f locustfile.py --host=http://localhost:8080 --users=50 --spawn-rate=10 --run-time=10m --headless --csv=results/cenario_a

# Cenário B: 100 usuários por 10 min  
locust -f locustfile.py --host=http://localhost:8080 --users=100 --spawn-rate=10 --run-time=10m --headless --csv=results/cenario_b

# Cenário C: 200 usuários por 5 min
locust -f locustfile.py --host=http://localhost:8080 --users=200 --spawn-rate=10 --run-time=5m --headless --csv=results/cenario_c
```

### Opção 3: Interface Web do Locust
```bash
locust -f locustfile.py --host=http://localhost:8080
```
Acesse http://localhost:8089 para controlar os testes via interface web.

## Análise dos Resultados

Após executar os testes, analise os resultados:
```bash
python analyze_results.py
```

Isso gerará:
- `analysis/performance_comparison.png` - Gráficos comparativos
- `analysis/relatorio_performance.txt` - Relatório detalhado em português

## Interpretação dos Resultados

### Arquivo CSV
Cada execução gera arquivos CSV com:
- `*_stats.csv`: Estatísticas agregadas por endpoint
- `*_failures.csv`: Detalhes dos erros ocorridos
- `*_exceptions.csv`: Exceções capturadas

### Métricas Importantes
- **Average Response Time**: Tempo médio de resposta em ms
- **Requests/s**: Throughput do sistema
- **Failure Count**: Número de requisições que falharam
- **50%/95%/99% Response Time**: Percentis de latência

### Indicadores de Performance
- **Tempo de resposta < 500ms**: Excelente
- **Taxa de sucesso > 99%**: Sistema estável
- **Throughput crescente**: Boa escalabilidade

## Configurações Avançadas

### Modificar Mix de Endpoints
Edite as anotações `@task(peso)` no arquivo `locustfile.py`:
```python
@task(40)  # 40% das requisições
def get_owners(self):
    # ...

@task(30)  # 30% das requisições  
def get_owner_by_id(self):
    # ...
```

### Ajustar Tempo de Espera
Modifique a linha no `locustfile.py`:
```python
wait_time = between(1, 3)  # Entre 1 a 3 segundos
```

### Configurar Diferentes Cenários
Edite o arquivo `run-tests.ps1` para ajustar:
- Número de usuários por cenário
- Duração dos testes
- Número de repetições
- URLs de destino

## Troubleshooting

### Aplicação não responde
Verifique se todos os containers estão rodando:
```bash
docker-compose ps
```

### Muitos erros nos testes
- Reduza o número de usuários
- Aumente o tempo entre requisições
- Verifique recursos do sistema (CPU/memória)

### Python/Locust não encontrado
Certifique-se de que o Python está no PATH e as dependências instaladas:
```bash
python --version
pip list | grep locust
```

## Estrutura dos Resultados

```
results/
├── CenarioA_20231018_143022_rep1/
│   ├── results_stats.csv
│   ├── results_failures.csv
│   └── results_exceptions.csv
├── CenarioB_20231018_144532_rep1/
└── CenarioC_20231018_150045_rep1/
```

## Observações Importantes

1. **Aquecimento**: O primeiro minuto de cada teste é descartado para aquecimento
2. **Repetições**: Execute múltiplas repetições para obter médias confiáveis
3. **Recursos**: Monitore CPU e memória durante os testes
4. **Rede**: Execute em rede local para eliminar latência externa
5. **Baseline**: Sempre estabeleça uma baseline antes de mudanças