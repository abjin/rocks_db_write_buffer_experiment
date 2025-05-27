#!/usr/bin/env python3
"""
RocksDB Write Buffer Size 최적화 실험 - 시나리오 1 결과 시각화
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
import matplotlib.patches as mpatches

# 한글 폰트 설정 (macOS용)
try:
    plt.rcParams['font.family'] = ['AppleGothic', 'Arial Unicode MS', 'DejaVu Sans']
except:
    plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 스타일 설정
try:
    plt.style.use('seaborn-v0_8')
except:
    plt.style.use('seaborn')
sns.set_palette("husl")

def create_performance_charts():
    """성능 지표 차트들을 생성합니다."""
    
    # 데이터 정의
    buffer_sizes = ['8MB', '32MB', '64MB', '256MB', '512MB']
    buffer_sizes_mb = [8, 32, 64, 256, 512]
    
    # 처리량 데이터
    throughput = [36705, 49841, 45076, 41576, 36910]
    processing_time = [32.69, 24.08, 26.62, 28.86, 32.51]
    relative_performance = [1.00, 1.36, 1.23, 1.13, 1.01]
    
    # 지연시간 데이터 (마이크로초)
    p50_latency = [56.29, 60.39, 70.61, 86.14, 96.83]
    p99_latency = [1336.88, 244.31, 294.26, 263.41, 333.45]
    p999_latency = [8521.80, 4221.43, 3870.78, 1383.95, 1543.58]
    
    # Compaction 데이터
    compact_read_gb = [2.60, 1.49, 0.97, 0.31, 0.30]
    compact_write_gb = [2.12, 1.07, 0.59, 0.17, 0.18]
    flush_write_gb = [0.72, 0.69, 0.62, 0.42, 0.30]
    write_amplification = [3.61, 2.17, 1.56, 0.55, 0.48]
    
    # Write Stall 데이터
    stall_time = [7.15, 0.00, 0.00, 0.00, 0.00]
    
    # 그래프 생성
    fig = plt.figure(figsize=(20, 24))
    
    # 1. 처리량 분석
    ax1 = plt.subplot(3, 3, 1)
    bars1 = ax1.bar(buffer_sizes, throughput, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax1.set_title('Write 처리량 (Operations per Second)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('처리량 (ops/sec)')
    ax1.set_xlabel('Write Buffer Size')
    
    # 최고값 표시
    max_idx = throughput.index(max(throughput))
    ax1.annotate(f'최고: {max(throughput):,} ops/sec', 
                xy=(max_idx, max(throughput)), 
                xytext=(max_idx, max(throughput) + 2000),
                ha='center', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    # 값 표시
    for i, v in enumerate(throughput):
        ax1.text(i, v + 500, f'{v:,}', ha='center', va='bottom', fontweight='bold')
    
    # 2. 상대적 성능 비교
    ax2 = plt.subplot(3, 3, 2)
    bars2 = ax2.bar(buffer_sizes, relative_performance, color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax2.set_title('상대적 성능 비교 (8MB 기준)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('상대적 성능 (배수)')
    ax2.set_xlabel('Write Buffer Size')
    ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='기준선 (8MB)')
    
    # 값 표시
    for i, v in enumerate(relative_performance):
        ax2.text(i, v + 0.02, f'{v:.2f}x', ha='center', va='bottom', fontweight='bold')
    
    ax2.legend()
    
    # 3. 지연시간 비교 (로그 스케일)
    ax3 = plt.subplot(3, 3, 3)
    x_pos = np.arange(len(buffer_sizes))
    width = 0.25
    
    bars3_1 = ax3.bar(x_pos - width, p50_latency, width, label='P50', alpha=0.8)
    bars3_2 = ax3.bar(x_pos, p99_latency, width, label='P99', alpha=0.8)
    bars3_3 = ax3.bar(x_pos + width, p999_latency, width, label='P99.9', alpha=0.8)
    
    ax3.set_title('Write 지연시간 분석 (로그 스케일)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('지연시간 (μs)')
    ax3.set_xlabel('Write Buffer Size')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(buffer_sizes)
    ax3.set_yscale('log')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Write Amplification 트렌드
    ax4 = plt.subplot(3, 3, 4)
    line4 = ax4.plot(buffer_sizes_mb, write_amplification, 'o-', linewidth=3, markersize=8, color='#e74c3c')
    ax4.set_title('Write Amplification 트렌드', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Write Amplification (배수)')
    ax4.set_xlabel('Write Buffer Size (MB)')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)
    
    # 값 표시
    for i, (x, y) in enumerate(zip(buffer_sizes_mb, write_amplification)):
        ax4.annotate(f'{y:.2f}x', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 5. Compaction 부하 분석
    ax5 = plt.subplot(3, 3, 5)
    x_pos = np.arange(len(buffer_sizes))
    width = 0.25
    
    bars5_1 = ax5.bar(x_pos - width, compact_read_gb, width, label='Compact Read', alpha=0.8)
    bars5_2 = ax5.bar(x_pos, compact_write_gb, width, label='Compact Write', alpha=0.8)
    bars5_3 = ax5.bar(x_pos + width, flush_write_gb, width, label='Flush Write', alpha=0.8)
    
    ax5.set_title('Compaction 부하 분석', fontsize=14, fontweight='bold')
    ax5.set_ylabel('데이터량 (GB)')
    ax5.set_xlabel('Write Buffer Size')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(buffer_sizes)
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Write Stall 분석
    ax6 = plt.subplot(3, 3, 6)
    colors = ['red' if x > 0 else 'green' for x in stall_time]
    bars6 = ax6.bar(buffer_sizes, stall_time, color=colors, alpha=0.7)
    ax6.set_title('Write Stall 발생 시간', fontsize=14, fontweight='bold')
    ax6.set_ylabel('Stall Time (초)')
    ax6.set_xlabel('Write Buffer Size')
    
    # 값 표시
    for i, v in enumerate(stall_time):
        if v > 0:
            ax6.text(i, v + 0.1, f'{v:.2f}초', ha='center', va='bottom', fontweight='bold', color='red')
        else:
            ax6.text(i, 0.1, 'Stall 없음', ha='center', va='bottom', fontweight='bold', color='green')
    
    # 7. 처리량 vs 메모리 사용량 트레이드오프
    ax7 = plt.subplot(3, 3, 7)
    scatter = ax7.scatter(buffer_sizes_mb, throughput, s=[x*2 for x in buffer_sizes_mb], 
                         c=write_amplification, cmap='RdYlBu_r', alpha=0.7)
    ax7.set_title('처리량 vs 메모리 사용량 트레이드오프', fontsize=14, fontweight='bold')
    ax7.set_ylabel('처리량 (ops/sec)')
    ax7.set_xlabel('Write Buffer Size (MB)')
    ax7.set_xscale('log')
    
    # 컬러바 추가
    cbar = plt.colorbar(scatter, ax=ax7)
    cbar.set_label('Write Amplification')
    
    # 최적점 표시
    optimal_idx = throughput.index(max(throughput))
    ax7.annotate('최적점', 
                xy=(buffer_sizes_mb[optimal_idx], throughput[optimal_idx]),
                xytext=(buffer_sizes_mb[optimal_idx]*2, throughput[optimal_idx]),
                arrowprops=dict(arrowstyle='->', color='red', lw=2),
                fontsize=12, fontweight='bold', color='red')
    
    # 8. 종합 성능 점수 (정규화된 지표들의 가중 평균)
    ax8 = plt.subplot(3, 3, 8)
    
    # 정규화 (높을수록 좋은 지표는 그대로, 낮을수록 좋은 지표는 역수)
    norm_throughput = np.array(throughput) / max(throughput)
    norm_latency = min(p99_latency) / np.array(p99_latency)  # 역수
    norm_write_amp = min(write_amplification) / np.array(write_amplification)  # 역수
    norm_stall = 1 - np.array(stall_time) / max(stall_time) if max(stall_time) > 0 else np.ones(len(stall_time))
    
    # 가중 평균 (처리량 40%, 지연시간 30%, Write Amplification 20%, Stall 10%)
    composite_score = (norm_throughput * 0.4 + norm_latency * 0.3 + 
                      norm_write_amp * 0.2 + norm_stall * 0.1)
    
    bars8 = ax8.bar(buffer_sizes, composite_score, 
                   color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
    ax8.set_title('종합 성능 점수', fontsize=14, fontweight='bold')
    ax8.set_ylabel('종합 점수 (0-1)')
    ax8.set_xlabel('Write Buffer Size')
    
    # 최고 점수 표시
    max_score_idx = list(composite_score).index(max(composite_score))
    ax8.annotate(f'최고: {max(composite_score):.3f}', 
                xy=(max_score_idx, max(composite_score)), 
                xytext=(max_score_idx, max(composite_score) + 0.05),
                ha='center', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    # 값 표시
    for i, v in enumerate(composite_score):
        ax8.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 9. 권장사항 요약
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    recommendations = [
        "🎯 일반 OLTP: 32MB (최고 처리량)",
        "⚡ 고성능: 64MB (균형점)",
        "💾 메모리 제약: 32MB (최소 권장)",
        "🔄 배치 처리: 256MB (낮은 Write Amp)",
        "",
        "❌ 피해야 할 설정:",
        "• 16MB 미만 (Write Stall 위험)",
        "• 512MB 이상 (성능 향상 없음)"
    ]
    
    for i, rec in enumerate(recommendations):
        ax9.text(0.05, 0.9 - i*0.1, rec, transform=ax9.transAxes, 
                fontsize=11, fontweight='bold' if rec.startswith(('🎯', '⚡', '💾', '🔄', '❌')) else 'normal')
    
    ax9.set_title('실무 적용 권장사항', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('scenario1_analysis_charts.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_summary_table():
    """요약 테이블을 생성합니다."""
    
    data = {
        'Write Buffer Size': ['8MB', '32MB', '64MB', '256MB', '512MB'],
        '처리량 (ops/sec)': [36705, 49841, 45076, 41576, 36910],
        'P99 지연시간 (μs)': [1336.88, 244.31, 294.26, 263.41, 333.45],
        'Write Amplification': [3.61, 2.17, 1.56, 0.55, 0.48],
        'Write Stall (초)': [7.15, 0.00, 0.00, 0.00, 0.00],
        '권장 용도': [
            '❌ 사용 금지',
            '🎯 일반 OLTP',
            '⚡ 고성능',
            '🔄 배치 처리',
            '❌ 비효율적'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # 테이블 시각화
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=df.values, colLabels=df.columns, 
                    cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2)
    
    # 헤더 스타일링
    for i in range(len(df.columns)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # 최적 설정 하이라이트 (32MB)
    for j in range(len(df.columns)):
        table[(2, j)].set_facecolor('#E8F5E8')
    
    plt.title('RocksDB Write Buffer Size 최적화 실험 - 종합 결과', 
             fontsize=16, fontweight='bold', pad=20)
    
    plt.savefig('scenario1_summary_table.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print("RocksDB Write Buffer Size 최적화 실험 - 시나리오 1 결과 시각화")
    print("=" * 60)
    
    print("📊 성능 차트 생성 중...")
    create_performance_charts()
    
    print("📋 요약 테이블 생성 중...")
    create_summary_table()
    
    print("✅ 모든 그래프가 생성되었습니다!")
    print("📁 저장된 파일:")
    print("  - scenario1_analysis_charts.png")
    print("  - scenario1_summary_table.png") 