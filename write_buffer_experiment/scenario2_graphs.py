import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import font_manager
import pandas as pd

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Data from the tables
max_write_buffers = [1, 2, 4, 8, 16]
memory_usage_mb = [64, 128, 256, 512, 1024]

# Performance data
throughput_ops_sec = [46135, 42865, 48197, 44685, 46562]
processing_time_sec = [26.01, 28.00, 24.90, 26.85, 25.77]
relative_performance = [1.00, 0.93, 1.04, 0.97, 1.01]

# Latency data (microseconds)
p50_latency = [72.14, 75.72, 66.41, 72.76, 72.80]
p99_latency = [249.63, 315.39, 247.39, 302.33, 247.96]
p999_latency = [2600.39, 3784.52, 3202.01, 3354.23, 3040.29]

# I/O data (GB)
compact_read_gb = [0.97, 0.97, 0.98, 0.98, 0.97]
compact_write_gb = [0.59, 0.59, 0.61, 0.62, 0.59]
flush_write_gb = [0.65, 0.65, 0.65, 0.65, 0.65]
write_amplification = [1.56, 1.56, 1.58, 1.60, 1.56]

# Create figure with subplots
fig = plt.figure(figsize=(20, 16))

# 1. Throughput vs Max Write Buffers
ax1 = plt.subplot(3, 3, 1)
bars1 = plt.bar(range(len(max_write_buffers)), throughput_ops_sec, 
                color=['#ff7f0e' if x == 4 else '#1f77b4' for x in max_write_buffers])
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Throughput (ops/sec)')
plt.title('Write Throughput by Buffer Count')
plt.xticks(range(len(max_write_buffers)), max_write_buffers)
plt.grid(True, alpha=0.3)
# Add value labels on bars
for i, v in enumerate(throughput_ops_sec):
    plt.text(i, v + 500, f'{v:,}', ha='center', va='bottom', fontsize=9)

# 2. Processing Time vs Max Write Buffers
ax2 = plt.subplot(3, 3, 2)
bars2 = plt.bar(range(len(max_write_buffers)), processing_time_sec,
                color=['#ff7f0e' if x == 4 else '#2ca02c' for x in max_write_buffers])
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Processing Time (seconds)')
plt.title('Processing Time by Buffer Count')
plt.xticks(range(len(max_write_buffers)), max_write_buffers)
plt.grid(True, alpha=0.3)
# Add value labels on bars
for i, v in enumerate(processing_time_sec):
    plt.text(i, v + 0.3, f'{v:.1f}s', ha='center', va='bottom', fontsize=9)

# 3. Memory Usage vs Max Write Buffers
ax3 = plt.subplot(3, 3, 3)
plt.plot(max_write_buffers, memory_usage_mb, 'o-', linewidth=2, markersize=8, color='#d62728')
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Memory Usage (MB)')
plt.title('Memory Usage by Buffer Count')
plt.grid(True, alpha=0.3)
plt.yscale('log')
# Add value labels
for i, (x, y) in enumerate(zip(max_write_buffers, memory_usage_mb)):
    plt.text(x, y * 1.1, f'{y}MB', ha='center', va='bottom', fontsize=9)

# 4. Latency Comparison
ax4 = plt.subplot(3, 3, 4)
x_pos = np.arange(len(max_write_buffers))
width = 0.25
plt.bar(x_pos - width, p50_latency, width, label='P50', alpha=0.8)
plt.bar(x_pos, p99_latency, width, label='P99', alpha=0.8)
plt.bar(x_pos + width, [x/10 for x in p999_latency], width, label='P99.9 (/10)', alpha=0.8)
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Latency (microseconds)')
plt.title('Latency Distribution by Buffer Count')
plt.xticks(x_pos, max_write_buffers)
plt.legend()
plt.grid(True, alpha=0.3)

# 5. Relative Performance
ax5 = plt.subplot(3, 3, 5)
bars5 = plt.bar(range(len(max_write_buffers)), relative_performance,
                color=['#ff7f0e' if x == 4 else '#9467bd' for x in max_write_buffers])
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Relative Performance')
plt.title('Relative Performance (1 buffer = 1.0x)')
plt.xticks(range(len(max_write_buffers)), max_write_buffers)
plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Baseline')
plt.grid(True, alpha=0.3)
plt.legend()
# Add value labels
for i, v in enumerate(relative_performance):
    plt.text(i, v + 0.01, f'{v:.2f}x', ha='center', va='bottom', fontsize=9)

# 6. I/O Operations
ax6 = plt.subplot(3, 3, 6)
x_pos = np.arange(len(max_write_buffers))
width = 0.25
plt.bar(x_pos - width, compact_read_gb, width, label='Compact Read', alpha=0.8)
plt.bar(x_pos, compact_write_gb, width, label='Compact Write', alpha=0.8)
plt.bar(x_pos + width, flush_write_gb, width, label='Flush Write', alpha=0.8)
plt.xlabel('Max Write Buffer Number')
plt.ylabel('I/O Volume (GB)')
plt.title('I/O Operations by Buffer Count')
plt.xticks(x_pos, max_write_buffers)
plt.legend()
plt.grid(True, alpha=0.3)

# 7. Write Amplification
ax7 = plt.subplot(3, 3, 7)
plt.plot(max_write_buffers, write_amplification, 'o-', linewidth=2, markersize=8, color='#8c564b')
plt.xlabel('Max Write Buffer Number')
plt.ylabel('Write Amplification Factor')
plt.title('Write Amplification by Buffer Count')
plt.grid(True, alpha=0.3)
plt.ylim(1.5, 1.65)
# Add value labels
for i, (x, y) in enumerate(zip(max_write_buffers, write_amplification)):
    plt.text(x, y + 0.005, f'{y:.2f}x', ha='center', va='bottom', fontsize=9)

# 8. Performance vs Memory Efficiency
ax8 = plt.subplot(3, 3, 8)
plt.scatter(memory_usage_mb, throughput_ops_sec, s=100, alpha=0.7)
for i, txt in enumerate(max_write_buffers):
    plt.annotate(f'{txt} buffers', (memory_usage_mb[i], throughput_ops_sec[i]), 
                xytext=(5, 5), textcoords='offset points', fontsize=9)
plt.xlabel('Memory Usage (MB)')
plt.ylabel('Throughput (ops/sec)')
plt.title('Performance vs Memory Trade-off')
plt.grid(True, alpha=0.3)
plt.xscale('log')

# 9. Summary Performance Radar Chart
ax9 = plt.subplot(3, 3, 9, projection='polar')
categories = ['Throughput', 'Low Latency', 'Memory Efficiency', 'I/O Efficiency']
# Normalize metrics (higher is better)
throughput_norm = [x/max(throughput_ops_sec) for x in throughput_ops_sec]
latency_norm = [1 - (x-min(p50_latency))/(max(p50_latency)-min(p50_latency)) for x in p50_latency]
memory_eff = [1/x for x in memory_usage_mb]
memory_eff_norm = [x/max(memory_eff) for x in memory_eff]
io_eff_norm = [1 - (x-min(write_amplification))/(max(write_amplification)-min(write_amplification)) for x in write_amplification]

angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
angles += angles[:1]  # Complete the circle

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
for i, buffers in enumerate(max_write_buffers):
    values = [throughput_norm[i], latency_norm[i], memory_eff_norm[i], io_eff_norm[i]]
    values += values[:1]  # Complete the circle
    ax9.plot(angles, values, 'o-', linewidth=2, label=f'{buffers} buffers', color=colors[i])
    ax9.fill(angles, values, alpha=0.1, color=colors[i])

ax9.set_xticks(angles[:-1])
ax9.set_xticklabels(categories)
ax9.set_ylim(0, 1)
ax9.set_title('Performance Profile Comparison', pad=20)
ax9.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

plt.tight_layout()
plt.savefig('write_buffer_experiment/scenario2_analysis_graphs.png', dpi=300, bbox_inches='tight')
plt.show()

# Create a separate detailed latency comparison chart
fig2, ax = plt.subplots(1, 1, figsize=(12, 8))
x_pos = np.arange(len(max_write_buffers))
width = 0.25

bars1 = ax.bar(x_pos - width, p50_latency, width, label='P50 Latency', alpha=0.8, color='#1f77b4')
bars2 = ax.bar(x_pos, p99_latency, width, label='P99 Latency', alpha=0.8, color='#ff7f0e')
bars3 = ax.bar(x_pos + width, [x/10 for x in p999_latency], width, label='P99.9 Latency (/10)', alpha=0.8, color='#2ca02c')

ax.set_xlabel('Max Write Buffer Number', fontsize=12)
ax.set_ylabel('Latency (microseconds)', fontsize=12)
ax.set_title('Detailed Latency Analysis by Buffer Count', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(max_write_buffers)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Add value labels on bars
for i, v in enumerate(p50_latency):
    ax.text(i - width, v + 2, f'{v:.1f}', ha='center', va='bottom', fontsize=9)
for i, v in enumerate(p99_latency):
    ax.text(i, v + 5, f'{v:.1f}', ha='center', va='bottom', fontsize=9)
for i, v in enumerate(p999_latency):
    ax.text(i + width, v/10 + 10, f'{v:.0f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('write_buffer_experiment/scenario2_latency_detail.png', dpi=300, bbox_inches='tight')
plt.show()

print("Graphs have been generated and saved as:")
print("1. scenario2_analysis_graphs.png - Main analysis dashboard")
print("2. scenario2_latency_detail.png - Detailed latency comparison") 