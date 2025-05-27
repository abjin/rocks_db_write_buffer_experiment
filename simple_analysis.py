#!/usr/bin/env python3
"""
RocksDB Write Buffer 실험 결과 간단 분석 스크립트
"""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def parse_result_file(file_path):
    """db_bench 결과 파일에서 성능 메트릭 추출"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 파일명에서 설정 정보 추출
        filename = Path(file_path).stem
        parts = filename.split('_')
        
        if len(parts) >= 5:
            benchmark_type = parts[0]
            write_buffer_size = int(parts[1])
            max_write_buffer_number = int(parts[2])
            min_write_buffer_number_to_merge = int(parts[3])
            iteration = int(parts[4].replace('iter', ''))
        else:
            return None
        
        # 성능 메트릭 추출
        throughput = 0
        latency = 0
        
        # fillrandom, readrandom, overwrite 결과 라인 찾기
        pattern = rf'{benchmark_type}\s*:\s*([\d.]+)\s*micros/op\s*([\d.]+)\s*ops/sec'
        match = re.search(pattern, content)
        
        if match:
            latency = float(match.group(1))
            throughput = float(match.group(2))
        
        return {
            'benchmark_type': benchmark_type,
            'write_buffer_size_mb': write_buffer_size // (1024 * 1024),
            'max_write_buffer_number': max_write_buffer_number,
            'min_write_buffer_number_to_merge': min_write_buffer_number_to_merge,
            'iteration': iteration,
            'throughput': throughput,
            'latency_us': latency
        }
    
    except Exception as e:
        print(f"파일 파싱 에러 {file_path}: {e}")
        return None

def load_all_results(results_dir="write_buffer_experiment/results"):
    """모든 결과 파일 로드"""
    results = []
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"결과 디렉토리가 없습니다: {results_dir}")
        return pd.DataFrame()
    
    for file_path in results_path.glob("*.txt"):
        result = parse_result_file(file_path)
        if result and result['throughput'] > 0:  # 유효한 결과만
            results.append(result)
    
    if not results:
        print("유효한 결과 파일이 없습니다.")
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    print(f"총 {len(df)}개의 유효한 실험 결과 로드")
    return df

def create_basic_analysis(df):
    """기본 분석 및 시각화"""
    if df.empty:
        return
    
    # 출력 디렉토리 생성
    output_dir = Path("write_buffer_experiment/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 기본 통계
    print("\n=== 기본 통계 ===")
    print(f"벤치마크 타입: {df['benchmark_type'].unique()}")
    print(f"Write Buffer 크기: {sorted(df['write_buffer_size_mb'].unique())}MB")
    print(f"처리량 범위: {df['throughput'].min():.0f} ~ {df['throughput'].max():.0f} ops/sec")
    print(f"지연시간 범위: {df['latency_us'].min():.2f} ~ {df['latency_us'].max():.2f} μs")
    
    # 2. fillrandom 기본 설정 분석
    fillrandom_basic = df[
        (df['benchmark_type'] == 'fillrandom') & 
        (df['max_write_buffer_number'] == 2) &
        (df['min_write_buffer_number_to_merge'] == 1)
    ]
    
    if not fillrandom_basic.empty:
        print("\n=== fillrandom 기본 설정 (2,1) 결과 ===")
        summary = fillrandom_basic.groupby('write_buffer_size_mb').agg({
            'throughput': ['mean', 'std'],
            'latency_us': ['mean', 'std']
        }).round(2)
        print(summary)
        
        # 최적 설정 찾기
        best_throughput = fillrandom_basic.groupby('write_buffer_size_mb')['throughput'].mean()
        optimal_size = best_throughput.idxmax()
        optimal_throughput = best_throughput.max()
        
        print(f"\n최적 Write Buffer Size: {optimal_size}MB")
        print(f"최대 처리량: {optimal_throughput:.0f} ops/sec")
    
    # 3. 간단한 시각화
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('RocksDB Write Buffer 실험 결과', fontsize=16, fontweight='bold')
    
    # 3-1. Write Buffer Size vs Throughput (fillrandom)
    if not fillrandom_basic.empty:
        throughput_avg = fillrandom_basic.groupby('write_buffer_size_mb')['throughput'].mean()
        ax1.plot(throughput_avg.index, throughput_avg.values, 'o-', linewidth=2, markersize=8)
        ax1.set_title('Throughput vs Write Buffer Size (fillrandom)')
        ax1.set_xlabel('Write Buffer Size (MB)')
        ax1.set_ylabel('Throughput (ops/sec)')
        ax1.grid(True, alpha=0.3)
        
        # 최적점 표시
        ax1.axvline(x=optimal_size, color='red', linestyle='--', alpha=0.7)
        ax1.text(optimal_size, optimal_throughput, f'최적: {optimal_size}MB', 
                rotation=90, verticalalignment='bottom', color='red')
    
    # 3-2. Latency vs Write Buffer Size
    if not fillrandom_basic.empty:
        latency_avg = fillrandom_basic.groupby('write_buffer_size_mb')['latency_us'].mean()
        ax2.plot(latency_avg.index, latency_avg.values, 's-', linewidth=2, markersize=8, color='orange')
        ax2.set_title('Latency vs Write Buffer Size (fillrandom)')
        ax2.set_xlabel('Write Buffer Size (MB)')
        ax2.set_ylabel('Latency (μs)')
        ax2.grid(True, alpha=0.3)
    
    # 3-3. 벤치마크 타입별 비교
    benchmark_comparison = df.groupby(['benchmark_type', 'write_buffer_size_mb'])['throughput'].mean().unstack(level=0)
    if not benchmark_comparison.empty:
        benchmark_comparison.plot(kind='bar', ax=ax3, width=0.8)
        ax3.set_title('Throughput by Benchmark Type')
        ax3.set_xlabel('Write Buffer Size (MB)')
        ax3.set_ylabel('Throughput (ops/sec)')
        ax3.legend(title='Benchmark Type')
        ax3.tick_params(axis='x', rotation=45)
    
    # 3-4. 메모리 효율성
    if not fillrandom_basic.empty:
        efficiency = fillrandom_basic.groupby('write_buffer_size_mb')['throughput'].mean() / fillrandom_basic.groupby('write_buffer_size_mb')['write_buffer_size_mb'].first()
        ax4.bar(efficiency.index, efficiency.values, alpha=0.7, color='green')
        ax4.set_title('Memory Efficiency (Throughput/MB)')
        ax4.set_xlabel('Write Buffer Size (MB)')
        ax4.set_ylabel('Efficiency (ops/sec/MB)')
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'simple_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\n시각화 저장: {output_dir / 'simple_analysis.png'}")
    
    # 4. CSV 저장
    df.to_csv(output_dir / 'simple_results.csv', index=False)
    print(f"결과 저장: {output_dir / 'simple_results.csv'}")

def main():
    print("🚀 RocksDB Write Buffer 실험 간단 분석 시작")
    
    # 결과 로드
    df = load_all_results()
    
    if df.empty:
        print("❌ 분석할 데이터가 없습니다.")
        return
    
    # 분석 실행
    create_basic_analysis(df)
    
    print("\n✅ 분석 완료!")

if __name__ == "__main__":
    main() 