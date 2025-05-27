#!/usr/bin/env python3
"""
RocksDB Min Write Buffer Number To Merge Optimization - Scenario 3 Visualization
Visualizes all tables from scenario3_analysis.md with English labels
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
import seaborn as sns

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Data from scenario3_analysis.md tables
merge_buffers = [1, 2, 4, 6, 8]
merge_labels = ['1 (Immediate)', '2 (Fast)', '4 (Normal)', '6 (Slow)', '8 (Delayed)']

# Table 2.1: Write Throughput Data
throughput_ops_sec = [46997, 43658, 44922, 38225, 40629]
processing_time_sec = [25.53, 27.49, 26.71, 31.39, 29.54]
relative_performance = [1.00, 0.93, 0.96, 0.81, 0.86]

# Table 2.2: Write Latency Data (microseconds)
p50_latency = [69.21, 78.61, 80.21, 91.54, 86.64]
p99_latency = [248.88, 277.48, 246.31, 345.09, 294.03]
p999_latency = [3235.82, 2655.03, 1597.32, 1827.27, 1776.01]

# Table 3.1: Compaction Load Data
compact_read_gb = [0.96, 0.64, 0.30, 0.19, 0.28]
compact_write_gb = [0.59, 0.32, 0.17, 0.09, 0.17]
flush_write_gb = [0.62, 0.56, 0.40, 0.39, 0.28]
write_amplification = [1.55, 0.88, 0.47, 0.28, 0.45]

# Table 3.2: Write Stall Data
stall_time_sec = [0.00, 0.00, 0.00, 0.06, 0.39]

# Create figure with subplots
fig = plt.figure(figsize=(20, 24))

# 1. Write Throughput Analysis
ax1 = plt.subplot(4, 2, 1)
bars1 = ax1.bar(merge_labels, throughput_ops_sec, color=['#2E8B57', '#4682B4', '#DAA520', '#CD853F', '#B22222'])
ax1.set_title('Write Throughput by Min Merge Buffers', fontsize=14, fontweight='bold')
ax1.set_xlabel('Min Write Buffer Number To Merge')
ax1.set_ylabel('Operations per Second')
ax1.grid(True, alpha=0.3)

# Add value labels on bars
for bar, value in zip(bars1, throughput_ops_sec):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 500,
             f'{value:,}', ha='center', va='bottom', fontweight='bold')

# Add performance degradation annotations
for i, (bar, perf) in enumerate(zip(bars1, relative_performance)):
    if i > 0:  # Skip the baseline
        degradation = (1 - perf) * 100
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height()/2,
                f'-{degradation:.0f}%', ha='center', va='center', 
                color='white', fontweight='bold', fontsize=10)

# 2. Processing Time
ax2 = plt.subplot(4, 2, 2)
bars2 = ax2.bar(merge_labels, processing_time_sec, color=['#2E8B57', '#4682B4', '#DAA520', '#CD853F', '#B22222'])
ax2.set_title('Processing Time by Min Merge Buffers', fontsize=14, fontweight='bold')
ax2.set_xlabel('Min Write Buffer Number To Merge')
ax2.set_ylabel('Processing Time (seconds)')
ax2.grid(True, alpha=0.3)

# Add value labels
for bar, value in zip(bars2, processing_time_sec):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{value:.1f}s', ha='center', va='bottom', fontweight='bold')

# 3. Write Latency Analysis
ax3 = plt.subplot(4, 2, 3)
x_pos = np.arange(len(merge_labels))
width = 0.25

bars3_1 = ax3.bar(x_pos - width, p50_latency, width, label='P50 Latency', color='#2E8B57', alpha=0.8)
bars3_2 = ax3.bar(x_pos, p99_latency, width, label='P99 Latency', color='#4682B4', alpha=0.8)
bars3_3 = ax3.bar(x_pos + width, [x/10 for x in p999_latency], width, label='P99.9 Latency (/10)', color='#DAA520', alpha=0.8)

ax3.set_title('Write Latency Distribution by Min Merge Buffers', fontsize=14, fontweight='bold')
ax3.set_xlabel('Min Write Buffer Number To Merge')
ax3.set_ylabel('Latency (microseconds)')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(merge_labels, rotation=45, ha='right')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Write Amplification
ax4 = plt.subplot(4, 2, 4)
bars4 = ax4.bar(merge_labels, write_amplification, color=['#B22222', '#CD853F', '#DAA520', '#2E8B57', '#4682B4'])
ax4.set_title('Write Amplification by Min Merge Buffers', fontsize=14, fontweight='bold')
ax4.set_xlabel('Min Write Buffer Number To Merge')
ax4.set_ylabel('Write Amplification Factor')
ax4.grid(True, alpha=0.3)

# Add value labels and efficiency indicators
for bar, value in zip(bars4, write_amplification):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
             f'{value:.2f}x', ha='center', va='bottom', fontweight='bold')
    
    # Color code efficiency
    if value < 0.5:
        efficiency = "Excellent"
        color = 'green'
    elif value < 1.0:
        efficiency = "Good"
        color = 'orange'
    else:
        efficiency = "Poor"
        color = 'red'
    
    ax4.text(bar.get_x() + bar.get_width()/2., height/2,
             efficiency, ha='center', va='center', 
             color=color, fontweight='bold', fontsize=9)

# 5. I/O Operations Breakdown
ax5 = plt.subplot(4, 2, 5)
x_pos = np.arange(len(merge_labels))
width = 0.25

bars5_1 = ax5.bar(x_pos - width, compact_read_gb, width, label='Compact Read', color='#FF6B6B', alpha=0.8)
bars5_2 = ax5.bar(x_pos, compact_write_gb, width, label='Compact Write', color='#4ECDC4', alpha=0.8)
bars5_3 = ax5.bar(x_pos + width, flush_write_gb, width, label='Flush Write', color='#45B7D1', alpha=0.8)

ax5.set_title('I/O Operations Breakdown by Min Merge Buffers', fontsize=14, fontweight='bold')
ax5.set_xlabel('Min Write Buffer Number To Merge')
ax5.set_ylabel('Data Volume (GB)')
ax5.set_xticks(x_pos)
ax5.set_xticklabels(merge_labels, rotation=45, ha='right')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. Write Stall Analysis
ax6 = plt.subplot(4, 2, 6)
colors = ['green' if x == 0 else 'orange' if x < 0.1 else 'red' for x in stall_time_sec]
bars6 = ax6.bar(merge_labels, stall_time_sec, color=colors, alpha=0.7)
ax6.set_title('Write Stall Time by Min Merge Buffers', fontsize=14, fontweight='bold')
ax6.set_xlabel('Min Write Buffer Number To Merge')
ax6.set_ylabel('Stall Time (seconds)')
ax6.grid(True, alpha=0.3)

# Add value labels and status
for bar, value in zip(bars6, stall_time_sec):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{value:.2f}s', ha='center', va='bottom', fontweight='bold')
    
    # Add status text
    if value == 0:
        status = "No Stall"
        text_color = 'green'
    elif value < 0.1:
        status = "Minor Stall"
        text_color = 'orange'
    else:
        status = "Stall Issue"
        text_color = 'red'
    
    if height > 0.05:  # Only show text if bar is tall enough
        ax6.text(bar.get_x() + bar.get_width()/2., height/2,
                 status, ha='center', va='center', 
                 color='white', fontweight='bold', fontsize=9, rotation=90)

# 7. Performance vs I/O Efficiency Trade-off
ax7 = plt.subplot(4, 2, 7)
scatter = ax7.scatter(write_amplification, throughput_ops_sec, 
                     s=[200, 150, 100, 80, 120], 
                     c=merge_buffers, cmap='viridis', alpha=0.7)

# Add labels for each point
for i, (wa, thr, label) in enumerate(zip(write_amplification, throughput_ops_sec, merge_labels)):
    ax7.annotate(f'merge={merge_buffers[i]}', (wa, thr), 
                xytext=(5, 5), textcoords='offset points', fontweight='bold')

ax7.set_title('Performance vs I/O Efficiency Trade-off', fontsize=14, fontweight='bold')
ax7.set_xlabel('Write Amplification (lower is better)')
ax7.set_ylabel('Throughput (ops/sec, higher is better)')
ax7.grid(True, alpha=0.3)

# Add quadrant labels
ax7.text(0.3, 45000, 'Ideal Zone\n(Low WA, High Perf)', 
         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7),
         ha='center', va='center', fontweight='bold')
ax7.text(1.4, 40000, 'Poor Zone\n(High WA, Low Perf)', 
         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7),
         ha='center', va='center', fontweight='bold')

# 8. Scenario Comparison Summary
ax8 = plt.subplot(4, 2, 8)

# Data for scenario comparison (from table 5.1)
scenarios = ['Buffer Size\n(Scenario 1)', 'Buffer Number\n(Scenario 2)', 'Merge Number\n(Scenario 3)']
max_improvement = [36, 4, 0]
max_degradation = [-1, -7, -19]
optimal_settings = ['32MB', '4 buffers', '1 merge']

x_pos = np.arange(len(scenarios))
width = 0.35

bars8_1 = ax8.bar(x_pos - width/2, max_improvement, width, label='Max Improvement (%)', 
                  color='green', alpha=0.7)
bars8_2 = ax8.bar(x_pos + width/2, max_degradation, width, label='Max Degradation (%)', 
                  color='red', alpha=0.7)

ax8.set_title('Performance Impact Comparison Across Scenarios', fontsize=14, fontweight='bold')
ax8.set_xlabel('Optimization Parameter')
ax8.set_ylabel('Performance Change (%)')
ax8.set_xticks(x_pos)
ax8.set_xticklabels(scenarios)
ax8.legend()
ax8.grid(True, alpha=0.3)
ax8.axhline(y=0, color='black', linestyle='-', alpha=0.3)

# Add value labels
for bar, value in zip(bars8_1, max_improvement):
    if value > 0:
        ax8.text(bar.get_x() + bar.get_width()/2., value + 1,
                 f'+{value}%', ha='center', va='bottom', fontweight='bold')

for bar, value in zip(bars8_2, max_degradation):
    if value < 0:
        ax8.text(bar.get_x() + bar.get_width()/2., value - 1,
                 f'{value}%', ha='center', va='top', fontweight='bold')

# Add optimal settings as text
for i, (pos, setting) in enumerate(zip(x_pos, optimal_settings)):
    ax8.text(pos, -25, f'Optimal: {setting}', ha='center', va='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7),
             fontweight='bold', fontsize=9)

plt.tight_layout(pad=3.0)

# Save the plot
plt.savefig('scenario3_analysis_graphs.png', dpi=300, bbox_inches='tight')
plt.show()

print("Scenario 3 analysis graphs have been generated and saved as 'scenario3_analysis_graphs.png'")
print("\nKey Insights from the Graphs:")
print("1. merge=1 provides the best performance (46,997 ops/sec)")
print("2. Higher merge values reduce performance but improve I/O efficiency")
print("3. merge=6 shows the worst performance degradation (-19%)")
print("4. Write amplification decreases significantly with higher merge values")
print("5. Write stalls occur only at merge=6 and merge=8")
print("6. Clear trade-off between performance and I/O efficiency") 