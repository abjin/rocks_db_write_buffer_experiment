#!/usr/bin/env python3
"""
RocksDB Write Buffer 최적화 실험 결과 분석 스크립트
작성자: 컴퓨터공학과 4학년
목적: 실험 결과 데이터 파싱, 분석 및 시각화
"""

import os
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

# 한글 폰트 설정 (발표용)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

class RocksDBResultAnalyzer:
    """RocksDB 실험 결과 분석 클래스"""
    
    def __init__(self, results_dir="write_buffer_experiment/results"):
        self.results_dir = Path(results_dir)
        self.logs_dir = Path("write_buffer_experiment/logs")
        self.output_dir = Path("write_buffer_experiment/analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        # 결과 저장용 데이터
        self.results_data = []
        self.summary_stats = {}
        
        print("🔍 RocksDB Write Buffer 실험 결과 분석기 시작")
        
    def parse_db_bench_output(self, file_path):
        """db_bench 출력 파일을 파싱하여 성능 지표 추출"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 파일 읽기 오류: {file_path} - {e}")
            return None
            
        metrics = {}
        
        # 처리량 (ops/sec) 추출
        throughput_match = re.search(r'(\d+)\s+ops/sec', content)
        if throughput_match:
            metrics['throughput'] = int(throughput_match.group(1))
        
        # 평균 지연시간 추출 (microseconds)
        avg_latency_match = re.search(r'Average:\s+([\d.]+)', content)
        if avg_latency_match:
            metrics['avg_latency_us'] = float(avg_latency_match.group(1))
            
        # P99 지연시간 추출
        p99_match = re.search(r'Percentiles: P50: ([\d.]+) P95: ([\d.]+) P99: ([\d.]+)', content)
        if p99_match:
            metrics['p50_latency_us'] = float(p99_match.group(1))
            metrics['p95_latency_us'] = float(p99_match.group(2))
            metrics['p99_latency_us'] = float(p99_match.group(3))
        
        # 메모리 사용량 추출
        mem_match = re.search(r'Block cache size:\s+([\d.]+)\s*MB', content)
        if mem_match:
            metrics['block_cache_mb'] = float(mem_match.group(1))
            
        # Write amplification 추출
        wa_match = re.search(r'Write amplification:\s+([\d.]+)', content)
        if wa_match:
            metrics['write_amplification'] = float(wa_match.group(1))
            
        # Compaction 통계 추출
        compaction_match = re.search(r'Compactions\s+Level\s+Files\s+Size.*?\n(.*?)\n', content, re.DOTALL)
        if compaction_match:
            # 간단한 compaction 파일 수 추출
            compact_files_match = re.search(r'Total files:\s+(\d+)', content)
            if compact_files_match:
                metrics['total_files'] = int(compact_files_match.group(1))
        
        return metrics
    
    def parse_filename(self, filename):
        """파일명에서 실험 설정 정보 추출"""
        # 예: fillrandom_134217728_2_1_iter1.txt
        pattern = r'(\w+)_(\d+)_(\d+)_(\d+)_iter(\d+)\.txt'
        match = re.match(pattern, filename)
        
        if not match:
            return None
            
        benchmark_type = match.group(1)
        write_buffer_size = int(match.group(2))
        max_write_buffer_number = int(match.group(3))
        min_write_buffer_number_to_merge = int(match.group(4))
        iteration = int(match.group(5))
        
        # 크기를 MB로 변환
        write_buffer_size_mb = write_buffer_size // (1024 * 1024)
        
        return {
            'benchmark_type': benchmark_type,
            'write_buffer_size_bytes': write_buffer_size,
            'write_buffer_size_mb': write_buffer_size_mb,
            'max_write_buffer_number': max_write_buffer_number,
            'min_write_buffer_number_to_merge': min_write_buffer_number_to_merge,
            'iteration': iteration
        }
    
    def load_all_results(self):
        """모든 실험 결과 파일 로드 및 파싱"""
        print("📊 실험 결과 파일 로딩 중...")
        
        if not self.results_dir.exists():
            print(f"❌ 결과 디렉토리를 찾을 수 없습니다: {self.results_dir}")
            return
            
        result_files = list(self.results_dir.glob("*.txt"))
        print(f"📁 총 {len(result_files)}개의 결과 파일 발견")
        
        for file_path in result_files:
            # 파일명에서 실험 설정 추출
            config = self.parse_filename(file_path.name)
            if not config:
                print(f"⚠️  파일명 파싱 실패: {file_path.name}")
                continue
                
            # 벤치마크 결과 파싱
            metrics = self.parse_db_bench_output(file_path)
            if not metrics:
                print(f"⚠️  결과 파싱 실패: {file_path.name}")
                continue
            
            # 데이터 결합
            result = {**config, **metrics}
            self.results_data.append(result)
            
        print(f"✅ {len(self.results_data)}개의 실험 결과 로드 완료")
        
        # 데이터프레임으로 변환
        if self.results_data:
            self.df = pd.DataFrame(self.results_data)
            print("📈 데이터프레임 생성 완료")
            self.save_raw_data()
        else:
            print("❌ 로드된 데이터가 없습니다.")
    
    def save_raw_data(self):
        """원시 데이터를 CSV 및 JSON으로 저장"""
        csv_path = self.output_dir / "experiment_results.csv"
        json_path = self.output_dir / "experiment_results.json"
        
        self.df.to_csv(csv_path, index=False)
        self.df.to_json(json_path, orient='records', indent=2)
        
        print(f"💾 원시 데이터 저장: {csv_path}, {json_path}")
    
    def calculate_statistics(self):
        """실험 결과 통계 계산"""
        print("📊 통계 분석 중...")
        
        if self.df.empty:
            print("❌ 분석할 데이터가 없습니다.")
            return
        
        # 반복 실험 결과 평균 계산
        groupby_cols = ['benchmark_type', 'write_buffer_size_mb', 'max_write_buffer_number', 'min_write_buffer_number_to_merge']
        
        self.summary_stats = self.df.groupby(groupby_cols).agg({
            'throughput': ['mean', 'std'],
            'avg_latency_us': ['mean', 'std'],
            'p99_latency_us': ['mean', 'std'],
            'write_amplification': ['mean', 'std']
        }).round(2)
        
        # 컬럼명 정리
        self.summary_stats.columns = ['_'.join(col).strip() for col in self.summary_stats.columns.values]
        self.summary_stats = self.summary_stats.reset_index()
        
        # 요약 통계 저장
        summary_path = self.output_dir / "summary_statistics.csv"
        self.summary_stats.to_csv(summary_path, index=False)
        
        print(f"📊 요약 통계 저장: {summary_path}")
    
    def create_visualizations(self):
        """실험 결과 시각화"""
        print("📈 시각화 생성 중...")
        
        if self.df.empty:
            return
        
        # 스타일 설정
        sns.set_style("whitegrid")
        
        # 1. Write Buffer Size vs Throughput (fillrandom 기준)
        self.plot_write_buffer_size_impact()
        
        # 2. 지연시간 분석
        self.plot_latency_analysis()
        
        # 3. 메모리 효율성 분석
        self.plot_memory_efficiency()
        
        # 4. 최적 조합 비교
        self.plot_optimal_combination()
        
        print("🎨 모든 시각화 완료")
    
    def plot_write_buffer_size_impact(self):
        """Write Buffer Size가 성능에 미치는 영향"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Write Buffer Size Impact Analysis', fontsize=16, fontweight='bold')
        
        # fillrandom 기준 기본 설정 (2, 1) 데이터만 필터링
        basic_config = self.df[
            (self.df['benchmark_type'] == 'fillrandom') & 
            (self.df['max_write_buffer_number'] == 2) &
            (self.df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        if basic_config.empty:
            print("⚠️  fillrandom 기본 설정 데이터가 없습니다.")
            return
        
        # 그룹별 평균 계산
        grouped = basic_config.groupby('write_buffer_size_mb').agg({
            'throughput': 'mean',
            'p99_latency_us': 'mean',
            'write_amplification': 'mean'
        }).reset_index()
        
        # 1. Throughput
        ax1.plot(grouped['write_buffer_size_mb'], grouped['throughput'], 
                marker='o', linewidth=2, markersize=8, color='#2E86AB')
        ax1.set_title('Throughput vs Write Buffer Size', fontweight='bold')
        ax1.set_xlabel('Write Buffer Size (MB)')
        ax1.set_ylabel('Throughput (ops/sec)')
        ax1.grid(True, alpha=0.3)
        
        # 최적점 표시
        max_throughput_idx = grouped['throughput'].idxmax()
        optimal_size = grouped.loc[max_throughput_idx, 'write_buffer_size_mb']
        optimal_throughput = grouped.loc[max_throughput_idx, 'throughput']
        ax1.annotate(f'최적점: {optimal_size}MB\n{optimal_throughput:,.0f} ops/sec', 
                    xy=(optimal_size, optimal_throughput),
                    xytext=(optimal_size + 50, optimal_throughput + 5000),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red', fontweight='bold')
        
        # 2. P99 Latency
        ax2.plot(grouped['write_buffer_size_mb'], grouped['p99_latency_us'], 
                marker='s', linewidth=2, markersize=8, color='#A23B72')
        ax2.set_title('P99 Latency vs Write Buffer Size', fontweight='bold')
        ax2.set_xlabel('Write Buffer Size (MB)')
        ax2.set_ylabel('P99 Latency (μs)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Write Amplification
        ax3.plot(grouped['write_buffer_size_mb'], grouped['write_amplification'], 
                marker='^', linewidth=2, markersize=8, color='#F18F01')
        ax3.set_title('Write Amplification vs Write Buffer Size', fontweight='bold')
        ax3.set_xlabel('Write Buffer Size (MB)')
        ax3.set_ylabel('Write Amplification')
        ax3.grid(True, alpha=0.3)
        
        # 4. 메모리 효율성 (Throughput per MB)
        grouped['efficiency'] = grouped['throughput'] / grouped['write_buffer_size_mb']
        ax4.bar(grouped['write_buffer_size_mb'], grouped['efficiency'], 
               color='#C73E1D', alpha=0.7)
        ax4.set_title('Memory Efficiency (Throughput per MB)', fontweight='bold')
        ax4.set_xlabel('Write Buffer Size (MB)')
        ax4.set_ylabel('Throughput per MB')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'write_buffer_size_impact.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_latency_analysis(self):
        """지연시간 상세 분석"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 기본 설정 데이터
        basic_data = self.df[
            (self.df['benchmark_type'] == 'fillrandom') & 
            (self.df['max_write_buffer_number'] == 2) &
            (self.df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        if basic_data.empty:
            return
        
        # 1. Box plot - 지연시간 분포
        sns.boxplot(data=basic_data, x='write_buffer_size_mb', y='p99_latency_us', ax=ax1)
        ax1.set_title('P99 Latency Distribution by Buffer Size', fontweight='bold')
        ax1.set_xlabel('Write Buffer Size (MB)')
        ax1.set_ylabel('P99 Latency (μs)')
        
        # 2. 벤치마크 타입별 비교
        comparison_data = self.df[
            (self.df['max_write_buffer_number'] == 2) &
            (self.df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        sns.lineplot(data=comparison_data, x='write_buffer_size_mb', y='p99_latency_us', 
                    hue='benchmark_type', marker='o', ax=ax2)
        ax2.set_title('P99 Latency by Benchmark Type', fontweight='bold')
        ax2.set_xlabel('Write Buffer Size (MB)')
        ax2.set_ylabel('P99 Latency (μs)')
        ax2.legend(title='Benchmark Type')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'latency_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_memory_efficiency(self):
        """메모리 효율성 분석"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 기본 설정 데이터에서 효율성 계산
        basic_data = self.df[
            (self.df['benchmark_type'] == 'fillrandom') & 
            (self.df['max_write_buffer_number'] == 2) &
            (self.df['min_write_buffer_number_to_merge'] == 1)
        ].copy()
        
        if basic_data.empty:
            return
        
        # 메모리 사용량 추정 (write_buffer_size * max_write_buffer_number)
        basic_data['total_memory_mb'] = basic_data['write_buffer_size_mb'] * basic_data['max_write_buffer_number']
        basic_data['memory_efficiency'] = basic_data['throughput'] / basic_data['total_memory_mb']
        
        # 평균 계산
        grouped = basic_data.groupby('write_buffer_size_mb').agg({
            'total_memory_mb': 'mean',
            'throughput': 'mean',
            'memory_efficiency': 'mean'
        }).reset_index()
        
        # 산점도
        scatter = ax.scatter(grouped['total_memory_mb'], grouped['throughput'], 
                           s=grouped['memory_efficiency']*1000, 
                           c=grouped['write_buffer_size_mb'], 
                           cmap='viridis', alpha=0.7, edgecolors='black')
        
        # 각 점에 라벨 추가
        for i, row in grouped.iterrows():
            ax.annotate(f'{int(row["write_buffer_size_mb"])}MB', 
                       (row['total_memory_mb'], row['throughput']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=10, fontweight='bold')
        
        ax.set_title('Memory Usage vs Throughput\n(Bubble size = Memory Efficiency)', 
                    fontweight='bold', fontsize=14)
        ax.set_xlabel('Total Memory Usage (MB)')
        ax.set_ylabel('Throughput (ops/sec)')
        ax.grid(True, alpha=0.3)
        
        # 컬러바 추가
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Write Buffer Size (MB)')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'memory_efficiency.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_optimal_combination(self):
        """최적 조합 비교 (128MB 기준)"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 128MB에서 다른 파라미터 조합 데이터
        optimal_data = self.df[
            (self.df['benchmark_type'] == 'fillrandom') & 
            (self.df['write_buffer_size_mb'] == 128)
        ].copy()
        
        if optimal_data.empty:
            print("⚠️  128MB 데이터가 없습니다.")
            return
        
        # 조합별 평균 계산
        optimal_grouped = optimal_data.groupby(['max_write_buffer_number', 'min_write_buffer_number_to_merge']).agg({
            'throughput': 'mean',
            'p99_latency_us': 'mean'
        }).reset_index()
        
        # 조합 라벨 생성
        optimal_grouped['combination'] = optimal_grouped.apply(
            lambda x: f"({int(x['max_write_buffer_number'])}, {int(x['min_write_buffer_number_to_merge'])})", axis=1
        )
        
        # 1. Throughput 비교
        bars1 = ax1.bar(optimal_grouped['combination'], optimal_grouped['throughput'], 
                       color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_title('Throughput by Buffer Configuration\n(Write Buffer Size = 128MB)', fontweight='bold')
        ax1.set_xlabel('(max_write_buffer_number, min_write_buffer_number_to_merge)')
        ax1.set_ylabel('Throughput (ops/sec)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Latency 비교
        bars2 = ax2.bar(optimal_grouped['combination'], optimal_grouped['p99_latency_us'], 
                       color='coral', alpha=0.7, edgecolor='black')
        ax2.set_title('P99 Latency by Buffer Configuration\n(Write Buffer Size = 128MB)', fontweight='bold')
        ax2.set_xlabel('(max_write_buffer_number, min_write_buffer_number_to_merge)')
        ax2.set_ylabel('P99 Latency (μs)')
        ax2.tick_params(axis='x', rotation=45)
        
        # 값 표시
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'optimal_combination.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self):
        """실험 보고서 생성"""
        print("📝 실험 보고서 생성 중...")
        
        if self.df.empty:
            print("❌ 보고서 생성할 데이터가 없습니다.")
            return
        
        report_path = self.output_dir / "experiment_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# RocksDB Write Buffer 최적화 실험 보고서\n\n")
            f.write(f"**생성일**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 실험 개요
            f.write("## 실험 개요\n\n")
            f.write(f"- **총 실험 횟수**: {len(self.df)}\n")
            f.write(f"- **벤치마크 타입**: {', '.join(self.df['benchmark_type'].unique())}\n")
            f.write(f"- **Write Buffer 크기 범위**: {self.df['write_buffer_size_mb'].min()}MB ~ {self.df['write_buffer_size_mb'].max()}MB\n\n")
            
            # 주요 발견사항
            f.write("## 주요 발견사항\n\n")
            
            # 최고 성능 설정 찾기
            best_fillrandom = self.df[self.df['benchmark_type'] == 'fillrandom'].nlargest(1, 'throughput')
            if not best_fillrandom.empty:
                best = best_fillrandom.iloc[0]
                f.write(f"### 최고 성능 설정 (fillrandom)\n")
                f.write(f"- **Write Buffer Size**: {best['write_buffer_size_mb']}MB\n")
                f.write(f"- **Max Write Buffer Number**: {best['max_write_buffer_number']}\n")
                f.write(f"- **Min Write Buffer Number To Merge**: {best['min_write_buffer_number_to_merge']}\n")
                f.write(f"- **처리량**: {best['throughput']:,.0f} ops/sec\n")
                f.write(f"- **P99 지연시간**: {best['p99_latency_us']:.1f} μs\n\n")
            
            # 통계 요약
            if hasattr(self, 'summary_stats') and not self.summary_stats.empty:
                f.write("## 통계 요약\n\n")
                f.write("### Write Buffer Size별 평균 성능 (fillrandom, 기본 설정)\n\n")
                
                basic_stats = self.summary_stats[
                    (self.summary_stats['benchmark_type'] == 'fillrandom') &
                    (self.summary_stats['max_write_buffer_number'] == 2) &
                    (self.summary_stats['min_write_buffer_number_to_merge'] == 1)
                ]
                
                f.write("| Buffer Size | Throughput | P99 Latency |\n")
                f.write("|-------------|------------|-------------|\n")
                for _, row in basic_stats.iterrows():
                    f.write(f"| {row['write_buffer_size_mb']}MB | {row['throughput_mean']:,.0f} ops/sec | {row['p99_latency_us_mean']:.1f} μs |\n")
                f.write("\n")
            
            # 결론
            f.write("## 결론\n\n")
            f.write("1. Write buffer 크기가 클수록 성능이 향상되지만, 특정 지점 이후부터는 감소\n")
            f.write("2. 메모리 사용량과 성능 간의 트레이드오프 확인\n")
            f.write("3. 최적 설정은 워크로드와 시스템 환경에 따라 달라짐\n\n")
            
            f.write("## 생성된 파일\n\n")
            f.write("- `experiment_results.csv`: 원시 실험 데이터\n")
            f.write("- `summary_statistics.csv`: 요약 통계\n")
            f.write("- `*.png`: 분석 그래프들\n")
        
        print(f"📋 실험 보고서 생성 완료: {report_path}")
    
    def run_analysis(self):
        """전체 분석 실행"""
        self.load_all_results()
        
        if self.df.empty:
            print("❌ 분석할 데이터가 없습니다. 실험을 먼저 실행해주세요.")
            return
        
        self.calculate_statistics()
        self.create_visualizations()
        self.generate_report()
        
        print("🎉 모든 분석 완료!")
        print(f"📁 결과 확인: {self.output_dir}")

def main():
    """메인 함수"""
    print("🚀 RocksDB Write Buffer 실험 결과 분석 시작\n")
    
    analyzer = RocksDBResultAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main() 