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
        pattern = f"{results_dir}/{scenario}_*/results_stats.csv"
        files = glob.glob(pattern)
        
        for file in files:
            try:
                df = pd.read_csv(file)
                df['scenario'] = scenario
                df['file_path'] = file
                scenarios[scenario].append(df)
            except Exception as e:
                print(f"Erro ao ler {file}: {e}")
    
    return scenarios

def calculate_scenario_stats(dfs):
    """Calcula estatísticas consolidadas para um cenário"""
    if not dfs:
        return None
    
    # Concatenar todos os DataFrames do cenário
    combined = pd.concat(dfs, ignore_index=True)
    
    # Filtrar apenas requisições (excluir agregados)
    requests_only = combined[combined['Type'] == 'GET'].copy() if 'Type' in combined.columns else combined
    
    stats = {
        'avg_response_time': requests_only['Average Response Time'].mean(),
        'max_response_time': requests_only['Max Response Time'].max(),
        'min_response_time': requests_only['Min Response Time'].min(),
        'median_response_time': requests_only['Median Response Time'].mean(),
        'avg_requests_per_sec': requests_only['Requests/s'].mean(),
        'total_requests': requests_only['Request Count'].sum(),
        'failure_count': requests_only['Failure Count'].sum(),
        'total_failure_count': requests_only['Failure Count'].sum(),
        'success_rate': ((requests_only['Request Count'].sum() - requests_only['Failure Count'].sum()) / 
                        requests_only['Request Count'].sum() * 100) if requests_only['Request Count'].sum() > 0 else 0,
        'repetitions': len(dfs)
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
        'repetitions': 'Repetições'
    }
    
    df_comparison = df_comparison.rename(columns=column_mapping)
    
    # Formatar números
    for col in ['Tempo Médio (ms)', 'Tempo Máximo (ms)', 'Tempo Mínimo (ms)', 'Tempo Mediano (ms)']:
        if col in df_comparison.columns:
            df_comparison[col] = df_comparison[col].round(2)
    
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
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Dados para os gráficos
    scenarios = list(scenario_stats.keys())
    users = [50, 100, 200]  # Usuários por cenário
    
    # Gráfico 1: Tempo de Resposta Médio
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    avg_times = [scenario_stats[s]['avg_response_time'] for s in scenarios]
    ax1.bar(scenarios, avg_times, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax1.set_title('Tempo Médio de Resposta por Cenário')
    ax1.set_ylabel('Tempo (ms)')
    ax1.set_xlabel('Cenário')
    
    # Gráfico 2: Throughput (Req/s)
    throughput = [scenario_stats[s]['avg_requests_per_sec'] for s in scenarios]
    ax2.bar(scenarios, throughput, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax2.set_title('Throughput Médio por Cenário')
    ax2.set_ylabel('Requisições/segundo')
    ax2.set_xlabel('Cenário')
    
    # Gráfico 3: Taxa de Sucesso
    success_rates = [scenario_stats[s]['success_rate'] for s in scenarios]
    ax3.bar(scenarios, success_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax3.set_title('Taxa de Sucesso por Cenário')
    ax3.set_ylabel('Taxa de Sucesso (%)')
    ax3.set_xlabel('Cenário')
    ax3.set_ylim(0, 100)
    
    # Gráfico 4: Escalabilidade (Usuários vs Throughput)
    ax4.plot(users, throughput, marker='o', linewidth=2, markersize=8)
    ax4.set_title('Escalabilidade: Usuários vs Throughput')
    ax4.set_xlabel('Número de Usuários')
    ax4.set_ylabel('Throughput (req/s)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gráficos salvos em {output_dir}/performance_comparison.png")

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
   • Cenário A (50 usuários): {cenario_a['avg_response_time']:.1f}ms em média
   • Cenário B (100 usuários): {cenario_b['avg_response_time']:.1f}ms em média  
   • Cenário C (200 usuários): {cenario_c['avg_response_time']:.1f}ms em média
   
   Ao dobrar os usuários de 50 para 100, o tempo médio {"aumentou" if cenario_b['avg_response_time'] > cenario_a['avg_response_time'] else "diminuiu"} {abs(cenario_b['avg_response_time'] - cenario_a['avg_response_time']):.1f}ms.
   No pico de 200 usuários, o tempo médio foi {cenario_c['avg_response_time'] - cenario_a['avg_response_time']:.1f}ms maior que o cenário base.

2. THROUGHPUT (REQUISIÇÕES POR SEGUNDO):
   • Cenário A: {cenario_a['avg_requests_per_sec']:.1f} req/s
   • Cenário B: {cenario_b['avg_requests_per_sec']:.1f} req/s
   • Cenário C: {cenario_c['avg_requests_per_sec']:.1f} req/s
   
   O sistema {"escala bem" if cenario_c['avg_requests_per_sec'] > cenario_a['avg_requests_per_sec'] else "não escala linearmente"} com o aumento de usuários.

3. CONFIABILIDADE:
   • Taxa de sucesso Cenário A: {cenario_a['success_rate']:.2f}%
   • Taxa de sucesso Cenário B: {cenario_b['success_rate']:.2f}% 
   • Taxa de sucesso Cenário C: {cenario_c['success_rate']:.2f}%
   
   {f"O sistema manteve alta confiabilidade em todos os cenários." if min(cenario_a['success_rate'], cenario_b['success_rate'], cenario_c['success_rate']) > 95 else "Houve degradação na confiabilidade com o aumento da carga."}

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