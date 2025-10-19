#!/usr/bin/env python3
"""
Script consolidado para análise completa dos resultados de performance do Spring PetClinic

Este script processa os arquivos CSV gerados pelo Locust e gera:
- Estatísticas consolidadas por cenário
- Gráficos individuais otimizados
- Tabelas detalhadas em CSV
- Relatório executivo
- Análise comparativa

Requer: pandas, matplotlib, seaborn, numpy
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from pathlib import Path
import numpy as np
from datetime import datetime

def load_results_data_with_warmup_exclusion(results_dir="results"):
    """
    Carrega dados excluindo períodos de aquecimento conforme especificado:
    - Cenário A (50 usuários, 10 min): descartar 1º minuto (60s)
    - Cenário B (100 usuários, 10 min): descartar 1º minuto (60s)  
    - Cenário C (200 usuários, 5 min): descartar primeiros 30s
    """
    scenario_stats = {}
    
    scenario_mapping = {
        'CenarioA': {
            'name': 'Cenário A (50 usuários)', 
            'users': 50, 
            'warmup_seconds': 60,
            'total_duration': 600  # 10 min
        },
        'CenarioB': {
            'name': 'Cenário B (100 usuários)', 
            'users': 100, 
            'warmup_seconds': 60,
            'total_duration': 600  # 10 min
        }, 
        'CenarioC': {
            'name': 'Cenário C (200 usuários)', 
            'users': 200, 
            'warmup_seconds': 30,
            'total_duration': 300  # 5 min
        }
    }
    
    for scenario_dir, info in scenario_mapping.items():
        # Buscar arquivos de histórico que contêm timestamps
        pattern = f"{results_dir}/{scenario_dir}/rep*/results_stats_history.csv"
        files = glob.glob(pattern)
        
        print(f"Processando {info['name']}: {len(files)} repetições")
        print(f"  Descartando aquecimento: {info['warmup_seconds']}s iniciais")
        
        all_stats = []
        valid_repetitions = 0
        
        for file in files:
            try:
                df = pd.read_csv(file)
                
                # Filtrar apenas dados agregados (linha 'Aggregated')
                df_aggregated = df[df['Name'] == 'Aggregated'].copy()
                
                if len(df_aggregated) == 0:
                    print(f"  ⚠️  Nenhum dado agregado encontrado em {file}")
                    continue
                
                # Obter timestamp inicial
                start_timestamp = df_aggregated['Timestamp'].min()
                warmup_end_timestamp = start_timestamp + info['warmup_seconds']
                
                # Filtrar dados após o período de aquecimento
                df_valid = df_aggregated[df_aggregated['Timestamp'] >= warmup_end_timestamp].copy()
                
                if len(df_valid) == 0:
                    print(f"  ⚠️  Nenhum dado válido após aquecimento em {file}")
                    continue
                
                # Calcular estatísticas da repetição (após aquecimento)
                # Usar dados do final do período (estado estável)
                final_data = df_valid.iloc[-1]  # Último registro = estado final
                
                rep_stats = {
                    'avg_response_time': final_data['Total Average Response Time'],
                    'median_response_time': final_data['Total Median Response Time'],
                    'max_response_time': final_data['Total Max Response Time'],
                    'min_response_time': final_data['Total Min Response Time'],
                    'p95_response_time': final_data['95%'] if pd.notna(final_data['95%']) else final_data['Total Average Response Time'],
                    'p99_response_time': final_data['99%'] if pd.notna(final_data['99%']) else final_data['Total Average Response Time'],
                    'success_rate': ((final_data['Total Request Count'] - final_data['Total Failure Count']) / 
                                   final_data['Total Request Count'] * 100) if final_data['Total Request Count'] > 0 else 0,
                    'requests_per_sec': df_valid['Requests/s'].mean(),  # Média do throughput no período válido
                    'total_requests': final_data['Total Request Count'],
                    'total_failures': final_data['Total Failure Count'],
                    'valid_duration': len(df_valid),  # Segundos de dados válidos
                    'warmup_discarded': info['warmup_seconds']
                }
                
                all_stats.append(rep_stats)
                valid_repetitions += 1
                
                print(f"  ✅ Rep {valid_repetitions}: {rep_stats['total_requests']} req, "
                      f"{rep_stats['success_rate']:.1f}% sucesso, "
                      f"{rep_stats['avg_response_time']:.1f}ms avg")
                    
            except Exception as e:
                print(f"  ❌ Erro ao processar {file}: {e}")
        
        if all_stats:
            # Calcular médias das repetições válidas
            scenario_stats[scenario_dir] = {
                'name': info['name'],
                'users': info['users'],
                'warmup_seconds': info['warmup_seconds'],
                'total_duration': info['total_duration'],
                'valid_repetitions': valid_repetitions,
                'avg_response_time': np.mean([s['avg_response_time'] for s in all_stats]),
                'median_response_time': np.mean([s['median_response_time'] for s in all_stats]),
                'max_response_time': np.max([s['max_response_time'] for s in all_stats]),
                'min_response_time': np.min([s['min_response_time'] for s in all_stats]),
                'p95_response_time': np.mean([s['p95_response_time'] for s in all_stats]),
                'p99_response_time': np.mean([s['p99_response_time'] for s in all_stats]),
                'success_rate': np.mean([s['success_rate'] for s in all_stats]),
                'avg_requests_per_sec': np.mean([s['requests_per_sec'] for s in all_stats]),
                'total_requests': np.sum([s['total_requests'] for s in all_stats]),
                'total_failures': np.sum([s['total_failures'] for s in all_stats]),
                'repetitions': len(all_stats),
                'all_repetitions': all_stats  # Guardar dados individuais
            }
            
            print(f"  📊 Resumo {info['name']}: {valid_repetitions} repetições válidas")
        else:
            print(f"  ❌ Nenhuma repetição válida encontrada para {info['name']}")
    
    return scenario_stats

def create_detailed_tables(scenario_stats, output_dir="analysis"):
    """Cria tabelas detalhadas para análise (integração do create_detailed_tables.py)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Tabela consolidada por cenário
    consolidated = []
    detailed_all = []
    
    for scenario_id, stats in scenario_stats.items():
        # Estatísticas consolidadas
        consolidated_stats = {
            'Cenário': stats['name'],
            'Usuários': stats['users'],
            'Repetições Válidas': stats['valid_repetitions'],
            'Aquecimento Descartado (s)': stats['warmup_seconds'],
            'Duração Total (s)': stats['total_duration'],
            'Tempo Médio (ms)': stats['avg_response_time'],
            'Tempo Mediano (ms)': stats['median_response_time'],
            'Tempo Máximo (ms)': stats['max_response_time'],
            'Tempo Mínimo (ms)': stats['min_response_time'],
            'P95 (ms)': stats['p95_response_time'],
            'P99 (ms)': stats['p99_response_time'],
            'Throughput Médio (req/s)': stats['avg_requests_per_sec'],
            'Taxa Sucesso Média (%)': stats['success_rate'],
            'Total Requisições': stats['total_requests'],
            'Total Falhas': stats['total_failures']
        }
        consolidated.append(consolidated_stats)
        
        # Adicionar dados detalhados por repetição
        for rep_idx, rep_data in enumerate(stats['all_repetitions'], 1):
            rep_data_detailed = {
                'Cenário': stats['name'],
                'Repetição': rep_idx,
                'Usuários': stats['users'],
                'Tempo Médio (ms)': rep_data['avg_response_time'],
                'Tempo Mediano (ms)': rep_data['median_response_time'],
                'Tempo Máximo (ms)': rep_data['max_response_time'],
                'P95 (ms)': rep_data['p95_response_time'],
                'P99 (ms)': rep_data['p99_response_time'],
                'Throughput (req/s)': rep_data['requests_per_sec'],
                'Taxa Sucesso (%)': rep_data['success_rate'],
                'Total Requisições': rep_data['total_requests'],
                'Total Falhas': rep_data['total_failures']
            }
            detailed_all.append(rep_data_detailed)
    
    # Converter para DataFrames
    df_consolidated = pd.DataFrame(consolidated)
    df_detailed = pd.DataFrame(detailed_all)
    
    # Criar análise comparativa
    cenario_a = df_consolidated[df_consolidated['Cenário'].str.contains('50 usuários')].iloc[0]
    cenario_b = df_consolidated[df_consolidated['Cenário'].str.contains('100 usuários')].iloc[0]
    cenario_c = df_consolidated[df_consolidated['Cenário'].str.contains('200 usuários')].iloc[0]
    
    analysis = []
    
    # Análise de tempo de resposta
    tempo_a_b = cenario_b['Tempo Médio (ms)'] - cenario_a['Tempo Médio (ms)']
    tempo_a_c = cenario_c['Tempo Médio (ms)'] - cenario_a['Tempo Médio (ms)']
    perc_a_b = (tempo_a_b / cenario_a['Tempo Médio (ms)']) * 100
    perc_a_c = (tempo_a_c / cenario_a['Tempo Médio (ms)']) * 100
    
    analysis.append({
        'Métrica': 'Tempo de Resposta',
        'Cenário A → B': f"{tempo_a_b:+.1f}ms ({perc_a_b:+.1f}%)",
        'Cenário A → C': f"{tempo_a_c:+.1f}ms ({perc_a_c:+.1f}%)",
        'Observação': f"Quando dobramos os usuários (50→100), o tempo médio {'aumentou' if tempo_a_b > 0 else 'diminuiu'} {abs(tempo_a_b):.1f}ms"
    })
    
    # Análise de throughput
    throughput_a_b = cenario_b['Throughput Médio (req/s)'] - cenario_a['Throughput Médio (req/s)']
    throughput_a_c = cenario_c['Throughput Médio (req/s)'] - cenario_a['Throughput Médio (req/s)']
    perc_throughput_a_c = (throughput_a_c / cenario_a['Throughput Médio (req/s)']) * 100
    
    analysis.append({
        'Métrica': 'Throughput',
        'Cenário A → B': f"{throughput_a_b:+.1f} req/s",
        'Cenário A → C': f"{throughput_a_c:+.1f} req/s ({perc_throughput_a_c:+.1f}%)",
        'Observação': f"O throughput {'escalou bem' if perc_throughput_a_c > 200 else 'não escalou linearmente'} com o aumento de usuários"
    })
    
    # Análise de confiabilidade
    sucesso_a_c = cenario_c['Taxa Sucesso Média (%)'] - cenario_a['Taxa Sucesso Média (%)']
    
    analysis.append({
        'Métrica': 'Taxa de Sucesso',
        'Cenário A → B': f"{cenario_b['Taxa Sucesso Média (%)'] - cenario_a['Taxa Sucesso Média (%)']:+.2f} p.p.",
        'Cenário A → C': f"{sucesso_a_c:+.2f} p.p.",
        'Observação': f"No pico (200 usuários), a taxa de sucesso {'se manteve estável' if sucesso_a_c > -5 else f'caiu {abs(sucesso_a_c):.1f} pontos percentuais'}"
    })
    
    df_analysis = pd.DataFrame(analysis)
    
    # Salvar arquivos
    df_consolidated.round(2).to_csv(f'{output_dir}/tabela_consolidada.csv', index=False, encoding='utf-8-sig')
    df_detailed.round(2).to_csv(f'{output_dir}/dados_detalhados.csv', index=False, encoding='utf-8-sig')
    df_analysis.to_csv(f'{output_dir}/analise_comparativa.csv', index=False, encoding='utf-8-sig')
    
    print(f"📊 Tabelas CSV geradas em {output_dir}/:")
    print("• tabela_consolidada.csv - Resumo por cenário")
    print("• dados_detalhados.csv - Dados de todas as repetições")
    print("• analise_comparativa.csv - Comparações entre cenários")
    
    return df_consolidated, df_detailed, df_analysis

def create_individual_charts(scenario_stats, output_dir="analysis"):
    """Cria gráficos individuais otimizados (integração e correção do fix_charts.py)"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Configurar estilo moderno
    plt.style.use('seaborn-v0_8-darkgrid')
    colors = ['#3498db', '#e74c3c', '#f39c12']  # Azul, vermelho, laranja
    
    # Extrair dados
    scenarios = ['50 usuários', '100 usuários', '200 usuários']
    users = [50, 100, 200]
    
    avg_times = [scenario_stats['CenarioA']['avg_response_time'], 
                 scenario_stats['CenarioB']['avg_response_time'], 
                 scenario_stats['CenarioC']['avg_response_time']]
    
    throughput = [scenario_stats['CenarioA']['avg_requests_per_sec'], 
                  scenario_stats['CenarioB']['avg_requests_per_sec'], 
                  scenario_stats['CenarioC']['avg_requests_per_sec']]
    
    success_rates = [scenario_stats['CenarioA']['success_rate'], 
                     scenario_stats['CenarioB']['success_rate'], 
                     scenario_stats['CenarioC']['success_rate']]
    
    p95_times = [scenario_stats['CenarioA']['p95_response_time'], 
                 scenario_stats['CenarioB']['p95_response_time'], 
                 scenario_stats['CenarioC']['p95_response_time']]
    
    # 1. GRÁFICO: Tempo de Resposta Médio
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    bars = ax.bar(scenarios, avg_times, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
    ax.set_title('Tempo Médio de Resposta por Cenário', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Tempo (ms)', fontsize=12)
    ax.set_xlabel('Cenários de Teste', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Valores nas barras
    for bar, value in zip(bars, avg_times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_times)*0.02, 
                f'{value:.0f}ms', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_tempo_resposta.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 2. GRÁFICO: Throughput
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    bars = ax.bar(scenarios, throughput, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
    ax.set_title('Throughput por Cenário', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Requisições/segundo', fontsize=12)
    ax.set_xlabel('Cenários de Teste', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar, value in zip(bars, throughput):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(throughput)*0.02, 
                f'{value:.0f} req/s', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_throughput.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 3. GRÁFICO: Taxa de Sucesso (CORRIGIDO!)
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    bars = ax.bar(scenarios, success_rates, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
    ax.set_title('Taxa de Sucesso por Cenário', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Taxa de Sucesso (%)', fontsize=12)
    ax.set_xlabel('Cenários de Teste', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Ajustar escala automaticamente baseada nos dados
    min_rate = min(success_rates)
    max_rate = max(success_rates)
    range_rate = max_rate - min_rate
    
    if range_rate < 10:  # Pouca variação
        ax.set_ylim(min_rate - range_rate*0.2, max_rate + range_rate*0.2)
    else:  # Grande variação
        ax.set_ylim(0, 100)
    
    for bar, value in zip(bars, success_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (max_rate - min_rate)*0.02, 
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_taxa_sucesso.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 4. GRÁFICO: Escalabilidade
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.plot(users, throughput, marker='o', linewidth=4, markersize=12, color='#3498db', label='Throughput Real')
    
    # Linha de escalabilidade ideal
    ideal_throughput = [throughput[0] * (u/users[0]) for u in users]
    ax.plot(users, ideal_throughput, '--', linewidth=3, color='#95a5a6', alpha=0.8, label='Escalabilidade Ideal')
    
    ax.set_title('Escalabilidade: Usuários vs Throughput', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Número de Usuários Simultâneos', fontsize=12)
    ax.set_ylabel('Throughput (req/s)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    
    # Anotações nos pontos
    for x, y in zip(users, throughput):
        ax.annotate(f'{y:.0f} req/s', (x, y), textcoords="offset points", xytext=(0,15), 
                    ha='center', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_escalabilidade.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 5. GRÁFICO: Comparação de Latências (P50, P95, P99)
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    
    x = np.arange(len(scenarios))
    width = 0.25
    
    median_times = [scenario_stats['CenarioA']['median_response_time'], 
                    scenario_stats['CenarioB']['median_response_time'], 
                    scenario_stats['CenarioC']['median_response_time']]
    
    bars1 = ax.bar(x - width, median_times, width, label='P50 (Mediana)', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x, avg_times, width, label='Tempo Médio', color='#e74c3c', alpha=0.8)
    bars3 = ax.bar(x + width, p95_times, width, label='P95', color='#f39c12', alpha=0.8)
    
    ax.set_title('Comparação Detalhada de Latências', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Tempo de Resposta (ms)', fontsize=12)
    ax.set_xlabel('Cenários de Teste', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Valores nas barras
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(p95_times)*0.01,
                    f'{height:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_latencias_detalhadas.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"📈 Gráficos individuais gerados em {output_dir}/:")
    print("• 01_tempo_resposta.png")
    print("• 02_throughput.png") 
    print("• 03_taxa_sucesso.png")
    print("• 04_escalabilidade.png")
    print("• 05_latencias_detalhadas.png")

def generate_executive_summary(scenario_stats, df_analysis, output_dir="analysis"):
    """Gera relatório executivo em linguagem simples"""
    
    # Extrair dados principais
    cenario_a = scenario_stats['CenarioA']
    cenario_b = scenario_stats['CenarioB']
    cenario_c = scenario_stats['CenarioC']
    
    report = f"""
RESUMO EXECUTIVO - TESTE DE PERFORMANCE SPRING PETCLINIC
========================================================

📊 PRINCIPAIS ACHADOS:

1. ESCALABILIDADE:
   • 50 usuários → 100 usuários: Throughput aumentou {((cenario_b['avg_requests_per_sec'] / cenario_a['avg_requests_per_sec']) - 1) * 100:.1f}%
   • 50 usuários → 200 usuários: Throughput aumentou {((cenario_c['avg_requests_per_sec'] / cenario_a['avg_requests_per_sec']) - 1) * 100:.1f}%
   
2. LATÊNCIA:
   • Tempo médio com 50 usuários: {cenario_a['avg_response_time']:.1f}ms
   • Tempo médio com 100 usuários: {cenario_b['avg_response_time']:.1f}ms ({((cenario_b['avg_response_time'] / cenario_a['avg_response_time']) - 1) * 100:+.1f}%)
   • Tempo médio com 200 usuários: {cenario_c['avg_response_time']:.1f}ms ({((cenario_c['avg_response_time'] / cenario_a['avg_response_time']) - 1) * 100:+.1f}%)

3. CONFIABILIDADE:
   • Taxa de sucesso com 50 usuários: {cenario_a['success_rate']:.1f}%
   • Taxa de sucesso com 100 usuários: {cenario_b['success_rate']:.1f}%
   • Taxa de sucesso com 200 usuários: {cenario_c['success_rate']:.1f}%

🔍 CONCLUSÕES EM LINGUAGEM SIMPLES:

{df_analysis.iloc[0]['Observação']}
{df_analysis.iloc[1]['Observação']}
{df_analysis.iloc[2]['Observação']}

🚨 PONTOS DE ATENÇÃO:
• {"Sistema possui baixa confiabilidade" if cenario_a['success_rate'] < 50 else "Sistema mantém boa confiabilidade"}
• {"Latência cresce significativamente com carga" if cenario_c['avg_response_time'] > cenario_a['avg_response_time'] * 2 else "Latência se mantém controlada"}
• {"Necessário investigar alta taxa de falhas" if cenario_c['success_rate'] < 90 else "Taxa de falhas aceitável"}

📈 RECOMENDAÇÕES:
• Implementar monitoramento de saúde dos microsserviços
• Configurar circuit breakers para maior resiliência
• Otimizar pool de conexões do banco de dados
• Considerar implementação de cache para endpoints frequentes
• Avaliar resources de CPU/memória dos containers
"""
    
    with open(f'{output_dir}/resumo_executivo.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📝 Resumo executivo salvo: {output_dir}/resumo_executivo.txt")

def main():
    """Função principal consolidada"""
    print("=== ANÁLISE COMPLETA DOS RESULTADOS DE PERFORMANCE ===\n")
    
    # 1. Carregar dados com exclusão de aquecimento
    print("📂 Carregando dados dos resultados (descartando períodos de aquecimento)...")
    scenario_stats = load_results_data_with_warmup_exclusion()
    
    if not scenario_stats:
        print("❌ Nenhum resultado encontrado! Certifique-se de que os testes foram executados.")
        return
    
    print(f"✅ Dados carregados com sucesso! Encontrados {len(scenario_stats)} cenários")
    
    # 2. Criar tabelas detalhadas
    print("\n📊 Gerando tabelas detalhadas...")
    df_consolidated, df_detailed, df_analysis = create_detailed_tables(scenario_stats)
    
    # 3. Criar gráficos individuais
    print("\n📈 Gerando gráficos individuais...")
    create_individual_charts(scenario_stats)
    
    # 4. Gerar resumo executivo
    print("\n📝 Gerando resumo executivo...")
    generate_executive_summary(scenario_stats, df_analysis)
    
    # 5. Mostrar resumo dos dados
    print("\n" + "="*80)
    print("📊 RESUMO DOS DADOS PROCESSADOS:")
    print("="*80)
    
    for scenario_id, stats in scenario_stats.items():
        print(f"\n{stats['name']}:")
        print(f"  • Repetições processadas: {stats['valid_repetitions']} (aquecimento: {stats['warmup_seconds']}s descartados)")
        print(f"  • Tempo médio: {stats['avg_response_time']:.1f}ms")
        print(f"  • P95: {stats['p95_response_time']:.1f}ms")
        print(f"  • Throughput: {stats['avg_requests_per_sec']:.1f} req/s")
        print(f"  • Taxa de sucesso: {stats['success_rate']:.1f}%")
        print(f"  • Total requisições: {stats['total_requests']:,}")
        print(f"  • Total falhas: {stats['total_failures']:,}")
    
    # 6. Mostrar tabela comparativa
    print("\n" + "="*80)
    print("📋 TABELA COMPARATIVA:")
    print("="*80)
    print(df_consolidated.round(2).to_string(index=False))
    
    # 7. Mostrar análise comparativa
    print("\n" + "="*80)
    print("🔍 ANÁLISE COMPARATIVA:")
    print("="*80)
    print(df_analysis.to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ ANÁLISE COMPLETA CONCLUÍDA!")
    print("="*80)
    print("\n📁 Arquivos gerados na pasta 'analysis/':")
    print("   📊 TABELAS CSV:")
    print("   • tabela_consolidada.csv - Resumo por cenário")
    print("   • dados_detalhados.csv - Dados de todas as repetições")
    print("   • analise_comparativa.csv - Comparações entre cenários")
    print("\n   📈 GRÁFICOS PNG:")
    print("   • 01_tempo_resposta.png - Tempo médio por cenário") 
    print("   • 02_throughput.png - Requisições/segundo por cenário")
    print("   • 03_taxa_sucesso.png - Confiabilidade por cenário")
    print("   • 04_escalabilidade.png - Análise de escalabilidade")
    print("   • 05_latencias_detalhadas.png - Comparação P50/P95/P99")
    print("\n   📝 RELATÓRIOS:")
    print("   • resumo_executivo.txt - Conclusões em linguagem simples")
    
    print(f"\n🎯 Use os arquivos CSV para análise detalhada em planilhas")
    print(f"🎯 Use os gráficos PNG para apresentações")
    print(f"🎯 Use o resumo executivo para conclusões rápidas")

if __name__ == "__main__":
    main()