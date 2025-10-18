#!/usr/bin/env python3
"""
Script para análise dos resultados dos testes de performance do Spring PetClinic

Este script processa os arquivos CSV gerados pelo Locust e gera:
- Estatísticas consolidadas por cenário
- Gráficos comparativos
- Relatório final em formato texto

Requer: pandas, matplotlib, seaborn
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime

def load_results_data(results_dir="results"):
    """Carrega todos os arquivos CSV de resultados"""
    scenarios = {"CenarioA": [], "CenarioB": [], "CenarioC": []}
    
    for scenario in scenarios.keys():
        # Buscar na estrutura: results/CenarioX/repY/results_stats.csv
        pattern = f"{results_dir}/{scenario}/rep*/results_stats.csv"
        files = glob.glob(pattern)
        
        print(f"Procurando arquivos para {scenario}: {pattern}")
        print(f"Encontrados {len(files)} arquivos")
        
        for file in files:
            try:
                df = pd.read_csv(file)
                # Filtrar apenas requisições individuais (não agregadas)
                df_filtered = df[df['Name'] != 'Aggregated'].copy()
                df_filtered['scenario'] = scenario
                df_filtered['file_path'] = file
                scenarios[scenario].append(df_filtered)
                print(f"  Carregado: {file} ({len(df_filtered)} linhas)")
            except Exception as e:
                print(f"Erro ao ler {file}: {e}")
    
    return scenarios

def calculate_scenario_stats(dfs):
    """Calcula estatísticas consolidadas para um cenário"""
    if not dfs:
        return None
    
    # Concatenar todos os DataFrames do cenário
    combined = pd.concat(dfs, ignore_index=True)
    
    # Calcular estatísticas agregadas por repetição
    stats = {
        'avg_response_time': combined['Average Response Time'].mean(),
        'max_response_time': combined['Max Response Time'].max(),
        'min_response_time': combined['Min Response Time'].min(),
        'median_response_time': combined['Median Response Time'].mean(),
        'avg_requests_per_sec': combined['Requests/s'].sum() / len(dfs),  # Soma por repetição, depois média
        'total_requests': combined['Request Count'].sum(),
        'failure_count': combined['Failure Count'].sum(),
        'success_rate': ((combined['Request Count'].sum() - combined['Failure Count'].sum()) / 
                        combined['Request Count'].sum() * 100) if combined['Request Count'].sum() > 0 else 0,
        'repetitions': len(dfs),
        'p95_response_time': combined['95%'].mean(),
        'p99_response_time': combined['99%'].mean()
    }
    
    return stats

def create_comparison_table(scenario_stats):
    """Cria tabela comparativa dos cenários"""
    df_comparison = pd.DataFrame(scenario_stats).T
    
    # Renomear colunas para português
    column_mapping = {
        'avg_response_time': 'Tempo Médio (ms)',
        'max_response_time': 'Tempo Máximo (ms)',
        'min_response_time': 'Tempo Mínimo (ms)',
        'median_response_time': 'Tempo Mediano (ms)',
        'avg_requests_per_sec': 'Req/s Médio',
        'total_requests': 'Total Requisições',
        'failure_count': 'Total Falhas',
        'success_rate': 'Taxa Sucesso (%)',
        'repetitions': 'Repetições',
        'p95_response_time': 'P95 (ms)',
        'p99_response_time': 'P99 (ms)'
    }
    
    df_comparison = df_comparison.rename(columns=column_mapping)
    
    # Adicionar informações sobre os cenários
    scenario_labels = ['Cenário A (50 usuários)', 'Cenário B (100 usuários)', 'Cenário C (200 usuários)']
    df_comparison.index = pd.Index(scenario_labels)
    
    # Formatar números
    for col in ['Tempo Médio (ms)', 'Tempo Máximo (ms)', 'Tempo Mínimo (ms)', 'Tempo Mediano (ms)', 'P95 (ms)', 'P99 (ms)']:
        if col in df_comparison.columns:
            df_comparison[col] = df_comparison[col].round(1)
    
    for col in ['Req/s Médio']:
        if col in df_comparison.columns:
            df_comparison[col] = df_comparison[col].round(1)
    
    for col in ['Taxa Sucesso (%)']:
        if col in df_comparison.columns:
            df_comparison[col] = df_comparison[col].round(2)
    
    return df_comparison

def create_charts(scenario_stats, output_dir="analysis"):
    """Cria gráficos comparativos"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Configurar estilo
    plt.style.use('default')
    
    # Dados para os gráficos
    scenarios = ['Cenário A\n(50 usuários)', 'Cenário B\n(100 usuários)', 'Cenário C\n(200 usuários)']
    users = [50, 100, 200]  # Usuários por cenário
    
    # Gráfico 1: Comparação de Performance
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise de Performance - Spring PetClinic Microservices', fontsize=16, fontweight='bold')
    
    # 1. Tempo de Resposta Médio
    avg_times = [scenario_stats['CenarioA']['avg_response_time'], 
                 scenario_stats['CenarioB']['avg_response_time'], 
                 scenario_stats['CenarioC']['avg_response_time']]
    
    bars1 = ax1.bar(scenarios, avg_times, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
    ax1.set_title('Tempo Médio de Resposta por Cenário', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Tempo (ms)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Adicionar valores nos barras
    for bar, value in zip(bars1, avg_times):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_times)*0.01, 
                f'{value:.1f}ms', ha='center', va='bottom', fontweight='bold')
    
    # 2. Throughput (Req/s)
    throughput = [scenario_stats['CenarioA']['avg_requests_per_sec'], 
                  scenario_stats['CenarioB']['avg_requests_per_sec'], 
                  scenario_stats['CenarioC']['avg_requests_per_sec']]
    
    bars2 = ax2.bar(scenarios, throughput, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
    ax2.set_title('Throughput por Cenário', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Requisições/segundo', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Adicionar valores nos barras
    for bar, value in zip(bars2, throughput):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(throughput)*0.01, 
                f'{value:.1f} req/s', ha='center', va='bottom', fontweight='bold')
    
    # 3. Taxa de Sucesso
    success_rates = [scenario_stats['CenarioA']['success_rate'], 
                     scenario_stats['CenarioB']['success_rate'], 
                     scenario_stats['CenarioC']['success_rate']]
    
    bars3 = ax3.bar(scenarios, success_rates, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
    ax3.set_title('Taxa de Sucesso por Cenário', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Taxa de Sucesso (%)', fontsize=12)
    ax3.set_ylim(95, 100.5)
    ax3.grid(True, alpha=0.3)
    
    # Adicionar valores nos barras
    for bar, value in zip(bars3, success_rates):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                f'{value:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    # 4. Escalabilidade (Usuários vs Throughput)
    ax4.plot(users, throughput, marker='o', linewidth=3, markersize=10, color='#2E86AB')
    ax4.set_title('Escalabilidade: Usuários vs Throughput', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Número de Usuários Simultâneos', fontsize=12)
    ax4.set_ylabel('Throughput (req/s)', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # Adicionar linha ideal de escalabilidade
    ideal_throughput = [throughput[0] * (u/users[0]) for u in users]
    ax4.plot(users, ideal_throughput, '--', color='gray', alpha=0.7, label='Escalabilidade Ideal')
    ax4.legend()
    
    # Adicionar valores nos pontos
    for x, y in zip(users, throughput):
        ax4.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico adicional: Percentis de Latência
    fig2, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    p95_times = [scenario_stats['CenarioA']['p95_response_time'], 
                 scenario_stats['CenarioB']['p95_response_time'], 
                 scenario_stats['CenarioC']['p95_response_time']]
    p99_times = [scenario_stats['CenarioA']['p99_response_time'], 
                 scenario_stats['CenarioB']['p99_response_time'], 
                 scenario_stats['CenarioC']['p99_response_time']]
    
    x = range(len(scenarios))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], avg_times, width, label='Tempo Médio', color='#2E86AB', alpha=0.8)
    bars2 = ax.bar([i + width/2 for i in x], p95_times, width, label='P95', color='#A23B72', alpha=0.8)
    
    ax.set_title('Comparação de Latências por Cenário', fontsize=16, fontweight='bold')
    ax.set_ylabel('Tempo de Resposta (ms)', fontsize=12)
    ax.set_xlabel('Cenários', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Adicionar valores
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + max(p95_times)*0.01,
                   f'{height:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/latency_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráficos salvos em {output_dir}/")
    print(f"  - performance_comparison.png")
    print(f"  - latency_comparison.png")

def generate_report(scenario_stats, comparison_table, output_dir="analysis"):
    """Gera relatório final em texto"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
RELATÓRIO DE PERFORMANCE - SPRING PETCLINIC MICROSERVICES
=========================================================

Data/Hora: {timestamp}

RESUMO DOS CENÁRIOS TESTADOS:
-----------------------------
• Cenário A: 50 usuários simultâneos por 10 minutos
• Cenário B: 100 usuários simultâneos por 10 minutos  
• Cenário C: 200 usuários simultâneos por 5 minutos

Mix de endpoints testados:
• GET /api/customer/owners (40% das requisições)
• GET /api/customer/owners/{{id}} (30% das requisições)
• GET /api/vet/vets (20% das requisições)
• POST /api/customer/owners (10% das requisições)

RESULTADOS CONSOLIDADOS:
-----------------------
{comparison_table.to_string()}

ANÁLISE COMPARATIVA:
-------------------

1. TEMPO DE RESPOSTA:
"""
    
    # Análise detalhada
    cenario_a = scenario_stats['CenarioA']
    cenario_b = scenario_stats['CenarioB'] 
    cenario_c = scenario_stats['CenarioC']
    
    report += f"""
   • Cenário A (50 usuários): {cenario_a['avg_response_time']:.1f}ms em média (P95: {cenario_a['p95_response_time']:.1f}ms)
   • Cenário B (100 usuários): {cenario_b['avg_response_time']:.1f}ms em média (P95: {cenario_b['p95_response_time']:.1f}ms)
   • Cenário C (200 usuários): {cenario_c['avg_response_time']:.1f}ms em média (P95: {cenario_c['p95_response_time']:.1f}ms)
   
   🔍 QUANDO DOBRAMOS OS USUÁRIOS (50→100): O tempo médio {"aumentou" if cenario_b['avg_response_time'] > cenario_a['avg_response_time'] else "diminuiu"} {abs(cenario_b['avg_response_time'] - cenario_a['avg_response_time']):.1f}ms ({((cenario_b['avg_response_time'] - cenario_a['avg_response_time'])/cenario_a['avg_response_time']*100):+.1f}%).
   🔍 NO PICO (200 usuários): O tempo médio foi {cenario_c['avg_response_time'] - cenario_a['avg_response_time']:+.1f}ms comparado ao cenário base ({((cenario_c['avg_response_time'] - cenario_a['avg_response_time'])/cenario_a['avg_response_time']*100):+.1f}%).

2. THROUGHPUT (REQUISIÇÕES POR SEGUNDO):
   • Cenário A: {cenario_a['avg_requests_per_sec']:.1f} req/s
   • Cenário B: {cenario_b['avg_requests_per_sec']:.1f} req/s ({((cenario_b['avg_requests_per_sec'] - cenario_a['avg_requests_per_sec'])/cenario_a['avg_requests_per_sec']*100):+.1f}%)
   • Cenário C: {cenario_c['avg_requests_per_sec']:.1f} req/s ({((cenario_c['avg_requests_per_sec'] - cenario_a['avg_requests_per_sec'])/cenario_a['avg_requests_per_sec']*100):+.1f}%)
   
   🔍 ESCALABILIDADE: {"O sistema escala bem" if cenario_c['avg_requests_per_sec'] > cenario_b['avg_requests_per_sec'] > cenario_a['avg_requests_per_sec'] else "O sistema não escala linearmente"} - cada duplicação de usuários resultou em {"aumento proporcional" if cenario_c['avg_requests_per_sec']/cenario_a['avg_requests_per_sec'] > 3 else "aumento menor que o esperado"} no throughput.

3. CONFIABILIDADE:
   • Taxa de sucesso Cenário A: {cenario_a['success_rate']:.2f}% ({cenario_a['failure_count']} falhas)
   • Taxa de sucesso Cenário B: {cenario_b['success_rate']:.2f}% ({cenario_b['failure_count']} falhas)
   • Taxa de sucesso Cenário C: {cenario_c['success_rate']:.2f}% ({cenario_c['failure_count']} falhas)
   
   🔍 NO PICO: A taxa de sucesso {"se manteve estável" if cenario_c['success_rate'] > 99 else f"caiu {cenario_a['success_rate'] - cenario_c['success_rate']:.2f} pontos percentuais"} quando chegamos a 200 usuários.

CONCLUSÕES:
----------
{generate_conclusions(scenario_stats)}

RECOMENDAÇÕES:
-------------
{generate_recommendations(scenario_stats)}
"""
    
    # Salvar relatório
    report_file = f"{output_dir}/relatorio_performance.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Relatório salvo em {report_file}")
    return report

def generate_conclusions(scenario_stats):
    """Gera conclusões automáticas baseadas nos dados"""
    cenario_a = scenario_stats['CenarioA']
    cenario_b = scenario_stats['CenarioB'] 
    cenario_c = scenario_stats['CenarioC']
    
    conclusions = []
    
    # Análise de escalabilidade
    if cenario_c['avg_requests_per_sec'] > cenario_a['avg_requests_per_sec'] * 1.5:
        conclusions.append("• O sistema demonstra boa escalabilidade, aumentando o throughput proporcionalmente aos usuários.")
    else:
        conclusions.append("• O sistema apresenta limitações de escalabilidade, não conseguindo manter o throughput proporcional ao aumento de usuários.")
    
    # Análise de latência  
    latency_increase = ((cenario_c['avg_response_time'] - cenario_a['avg_response_time']) / cenario_a['avg_response_time']) * 100
    if latency_increase < 50:
        conclusions.append("• O tempo de resposta se mantém estável mesmo com aumento significativo de carga.")
    else:
        conclusions.append(f"• Houve degradação significativa no tempo de resposta ({latency_increase:.1f}% de aumento) sob alta carga.")
    
    # Análise de confiabilidade
    min_success = min(cenario_a['success_rate'], cenario_b['success_rate'], cenario_c['success_rate'])
    if min_success > 99:
        conclusions.append("• O sistema mantém excelente confiabilidade (>99% sucesso) em todos os cenários.")
    elif min_success > 95:
        conclusions.append("• O sistema mantém boa confiabilidade (>95% sucesso) mesmo sob carga.")
    else:
        conclusions.append("• A confiabilidade do sistema é comprometida sob alta carga.")
    
    return "\n".join(conclusions)

def generate_recommendations(scenario_stats):
    """Gera recomendações baseadas nos resultados"""
    cenario_c = scenario_stats['CenarioC']
    
    recommendations = []
    
    if cenario_c['avg_response_time'] > 1000:
        recommendations.append("• Considerar otimização de consultas ao banco de dados e cache.")
    
    if cenario_c['success_rate'] < 99:
        recommendations.append("• Implementar circuit breakers e retry policies mais robustos.")
        
    if cenario_c['avg_requests_per_sec'] < 100:
        recommendations.append("• Avaliar configuração de pool de conexões e recursos de CPU/memória.")
    
    recommendations.append("• Realizar testes com carga sustentada por períodos mais longos.")
    recommendations.append("• Monitorar métricas de infraestrutura (CPU, memória, I/O) durante os testes.")
    
    return "\n".join(recommendations)

def main():
    """Função principal"""
    print("Iniciando análise dos resultados de performance...")
    
    # Carregar dados
    results = load_results_data()
    
    # Calcular estatísticas por cenário
    scenario_stats = {}
    for scenario, dfs in results.items():
        stats = calculate_scenario_stats(dfs)
        if stats:
            scenario_stats[scenario] = stats
            print(f"Processado {scenario}: {stats['repetitions']} repetições")
    
    if not scenario_stats:
        print("Nenhum resultado encontrado! Certifique-se de que os testes foram executados.")
        return
    
    # Criar tabela comparativa
    comparison_table = create_comparison_table(scenario_stats)
    print("\nTabela Comparativa:")
    print(comparison_table)
    
    # Criar gráficos
    create_charts(scenario_stats)
    
    # Gerar relatório
    report = generate_report(scenario_stats, comparison_table)
    
    print("\nAnálise concluída! Arquivos gerados na pasta 'analysis'")

if __name__ == "__main__":
    main()