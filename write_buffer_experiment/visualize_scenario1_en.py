#!/usr/bin/env python3
"""
RocksDB Write Buffer Size Optimization Experiment - Scenario 1 Results Visualization
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.patches as mpatches

# Style settings
try:
    plt.style.use('seaborn-v0_8')
except:
    plt.style.use('seaborn')
sns.set_palette("husl")

def create_performance_charts():
    """Create performance metric charts."""
    
    # Data definition
    buffer_sizes = ['8MB', '32MB', '64MB', '256MB', '512MB']
    buffer_sizes_mb = [8, 32, 64, 256, 512]
    
    # Throughput data
    throughput = [36705, 49841, 45076, 41576, 36910]
    processing_time = [32.69, 24.08, 26.62, 28.86, 32.51]
    relative_performance = [1.00, 1.36, 1.23, 1.13, 1.01]
    
    # Latency data (microseconds)
    p50_latency = [56.29, 60.39, 70.61, 86.14, 96.83]
    p99_latency = [1336.88, 244.31, 294.26, 263.41, 333.45]
    p999_latency = [8521.80, 4221.43, 3870.78, 1383.95, 1543.58]
    
    # Compaction data
    compact_read_gb = [2.60, 1.49, 0.97, 0.31, 0.30]
    compact_write_gb = [2.12, 1.07, 0.59, 0.17, 0.18]
    flush_write_gb = [0.72, 0.69, 0.62, 0.42, 0.30]
    write_amplification = [3.61, 2.17, 1.56, 0.55, 0.48]
    
    # Write Stall data
    stall_time = [7.15, 0.00, 0.00, 0.00, 0.00]
    
    # Create graphs
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Throughput Analysis
    ax1 = plt.subplot(3, 3, 1)
    bars1 = ax1.bar(buffer_sizes, throughput, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax1.set_title('Write Throughput (Operations per Second)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Throughput (ops/sec)')
    ax1.set_xlabel('Write Buffer Size')
    
    # Mark highest value
    max_idx = throughput.index(max(throughput))
    ax1.annotate(f'Peak: {max(throughput):,} ops/sec', 
                xy=(max_idx, max(throughput)), 
                xytext=(max_idx, max(throughput) + 2000),
                ha='center', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    # Show values
    for i, v in enumerate(throughput):
        ax1.text(i, v + 500, f'{v:,}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Relative Performance Comparison
    ax2 = plt.subplot(3, 3, 2)
    bars2 = ax2.bar(buffer_sizes, relative_performance, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax2.set_title('Relative Performance (8MB baseline)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Relative Performance (x)')
    ax2.set_xlabel('Write Buffer Size')
    ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Baseline (8MB)')
    
    # Show values
    for i, v in enumerate(relative_performance):
        ax2.text(i, v + 0.02, f'{v:.2f}x', ha='center', va='bottom', fontweight='bold')
    
    ax2.legend()
    
    # 3. Latency Comparison (Log Scale)
    ax3 = plt.subplot(3, 3, 3)
    x_pos = np.arange(len(buffer_sizes))
    width = 0.25
    
    bars3_1 = ax3.bar(x_pos - width, p50_latency, width, label='P50', alpha=0.8)
    bars3_2 = ax3.bar(x_pos, p99_latency, width, label='P99', alpha=0.8)
    bars3_3 = ax3.bar(x_pos + width, p999_latency, width, label='P99.9', alpha=0.8)
    
    ax3.set_title('Write Latency Analysis (Log Scale)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Latency (μs)')
    ax3.set_xlabel('Write Buffer Size')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(buffer_sizes)
    ax3.set_yscale('log')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Write Amplification Trend
    ax4 = plt.subplot(3, 3, 4)
    line4 = ax4.plot(buffer_sizes_mb, write_amplification, 'o-', linewidth=3, markersize=8, color='#e74c3c')
    ax4.set_title('Write Amplification Trend', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Write Amplification (x)')
    ax4.set_xlabel('Write Buffer Size (MB)')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)
    
    # Show values
    for i, (x, y) in enumerate(zip(buffer_sizes_mb, write_amplification)):
        ax4.annotate(f'{y:.2f}x', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 5. Compaction Load Analysis
    ax5 = plt.subplot(3, 3, 5)
    x_pos = np.arange(len(buffer_sizes))
    width = 0.25
    
    bars5_1 = ax5.bar(x_pos - width, compact_read_gb, width, label='Compact Read', alpha=0.8)
    bars5_2 = ax5.bar(x_pos, compact_write_gb, width, label='Compact Write', alpha=0.8)
    bars5_3 = ax5.bar(x_pos + width, flush_write_gb, width, label='Flush Write', alpha=0.8)
    
    ax5.set_title('Compaction Load Analysis', fontsize=14, fontweight='bold')
    ax5.set_ylabel('Data Volume (GB)')
    ax5.set_xlabel('Write Buffer Size')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(buffer_sizes)
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Write Stall Analysis
    ax6 = plt.subplot(3, 3, 6)
    colors = ['red' if x > 0 else 'green' for x in stall_time]
    bars6 = ax6.bar(buffer_sizes, stall_time, color=colors, alpha=0.7)
    ax6.set_title('Write Stall Occurrence Time', fontsize=14, fontweight='bold')
    ax6.set_ylabel('Stall Time (seconds)')
    ax6.set_xlabel('Write Buffer Size')
    
    # Show values
    for i, v in enumerate(stall_time):
        if v > 0:
            ax6.text(i, v + 0.1, f'{v:.2f}s', ha='center', va='bottom', fontweight='bold', color='red')
        else:
            ax6.text(i, 0.1, 'No Stall', ha='center', va='bottom', fontweight='bold', color='green')
    
    # 7. Throughput vs Memory Usage Trade-off
    ax7 = plt.subplot(3, 3, 7)
    scatter = ax7.scatter(buffer_sizes_mb, throughput, s=[x*2 for x in buffer_sizes_mb], 
                         c=write_amplification, cmap='RdYlBu_r', alpha=0.7)
    ax7.set_title('Throughput vs Memory Usage Trade-off', fontsize=14, fontweight='bold')
    ax7.set_ylabel('Throughput (ops/sec)')
    ax7.set_xlabel('Write Buffer Size (MB)')
    ax7.set_xscale('log')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax7)
    cbar.set_label('Write Amplification')
    
    # Mark optimal point
    optimal_idx = throughput.index(max(throughput))
    ax7.annotate('Optimal Point', 
                xy=(buffer_sizes_mb[optimal_idx], throughput[optimal_idx]),
                xytext=(buffer_sizes_mb[optimal_idx]*2, throughput[optimal_idx]),
                arrowprops=dict(arrowstyle='->', color='red', lw=2),
                fontsize=12, fontweight='bold', color='red')
    
    # 8. Composite Performance Score (weighted average of normalized metrics)
    ax8 = plt.subplot(3, 3, 8)
    
    # Normalize (higher is better for some metrics, lower is better for others)
    norm_throughput = np.array(throughput) / max(throughput)
    norm_latency = min(p99_latency) / np.array(p99_latency)  # inverse
    norm_write_amp = min(write_amplification) / np.array(write_amplification)  # inverse
    norm_stall = 1 - np.array(stall_time) / max(stall_time) if max(stall_time) > 0 else np.ones(len(stall_time))
    
    # Weighted average (Throughput 40%, Latency 30%, Write Amplification 20%, Stall 10%)
    composite_score = (norm_throughput * 0.4 + norm_latency * 0.3 + 
                      norm_write_amp * 0.2 + norm_stall * 0.1)
    
    bars8 = ax8.bar(buffer_sizes, composite_score, 
                   color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax8.set_title('Composite Performance Score', fontsize=14, fontweight='bold')
    ax8.set_ylabel('Composite Score (0-1)')
    ax8.set_xlabel('Write Buffer Size')
    
    # Mark highest score
    max_score_idx = list(composite_score).index(max(composite_score))
    ax8.annotate(f'Best: {max(composite_score):.3f}', 
                xy=(max_score_idx, max(composite_score)), 
                xytext=(max_score_idx, max(composite_score) + 0.05),
                ha='center', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    # Show values
    for i, v in enumerate(composite_score):
        ax8.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 9. Recommendations Summary
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    recommendations = [
        "🎯 General OLTP: 32MB (Best throughput)",
        "⚡ High Performance: 64MB (Balanced)",
        "💾 Memory Constrained: 32MB (Min recommended)",
        "🔄 Batch Processing: 256MB (Low Write Amp)",
        "",
        "❌ Avoid these settings:",
        "• Below 16MB (Write Stall risk)",
        "• Above 512MB (No performance gain)"
    ]
    
    for i, rec in enumerate(recommendations):
        weight = 'bold' if rec.startswith(('🎯', '⚡', '💾', '🔄', '❌')) else 'normal'
        ax9.text(0.05, 0.9 - i*0.1, rec, transform=ax9.transAxes, 
                fontsize=11, fontweight=weight)
    
    ax9.set_title('Practical Recommendations', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('scenario1_analysis_charts.png', dpi=300, bbox_inches='tight')
    print("✅ Performance charts saved as 'scenario1_analysis_charts.png'")

def create_summary_table():
    """Create summary table."""
    
    data = {
        'Write Buffer Size': ['8MB', '32MB', '64MB', '256MB', '512MB'],
        'Throughput (ops/sec)': [36705, 49841, 45076, 41576, 36910],
        'P99 Latency (μs)': [1336.88, 244.31, 294.26, 263.41, 333.45],
        'Write Amplification': [3.61, 2.17, 1.56, 0.55, 0.48],
        'Write Stall (sec)': [7.15, 0.00, 0.00, 0.00, 0.00],
        'Recommended Use': [
            '❌ Do not use',
            '🎯 General OLTP',
            '⚡ High Performance',
            '🔄 Batch Processing',
            '❌ Inefficient'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Table visualization
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=df.values, colLabels=df.columns, 
                    cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2)
    
    # Header styling
    for i in range(len(df.columns)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Highlight optimal setting (32MB)
    for j in range(len(df.columns)):
        table[(2, j)].set_facecolor('#E8F5E8')
    
    plt.title('RocksDB Write Buffer Size Optimization - Summary Results', 
             fontsize=16, fontweight='bold', pad=20)
    
    plt.savefig('scenario1_summary_table.png', dpi=300, bbox_inches='tight')
    print("✅ Summary table saved as 'scenario1_summary_table.png'")

if __name__ == "__main__":
    print("RocksDB Write Buffer Size Optimization Experiment - Scenario 1 Visualization")
    print("=" * 80)
    
    print("📊 Creating performance charts...")
    create_performance_charts()
    
    print("📋 Creating summary table...")
    create_summary_table()
    
    print("\n✅ All graphs have been generated!")
    print("📁 Generated files:")
    print("  - scenario1_analysis_charts.png")
    print("  - scenario1_summary_table.png") 