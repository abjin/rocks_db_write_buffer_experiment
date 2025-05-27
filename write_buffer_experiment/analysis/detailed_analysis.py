#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RocksDB Write Buffer 최적화 실험 결과 분석
작성자: 컴퓨터공학과 4학년
목적: 실험 결과 종합 분석 및 시각화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Malgun Gothic']
plt.rcParams['axes.unicode_minus'] = False

class RocksDBAnalyzer:
    def __init__(self, data_dir="./"):
        self.data_dir = Path(data_dir)
        self.results_df = None
        self.summary_df = None
        self.load_data()
        
    def load_data(self):
        """실험 결과 데이터 로드"""
        try:
            # CSV 데이터 로드
            self.results_df = pd.read_csv(self.data_dir / "experiment_results.csv")
            self.summary_df = pd.read_csv(self.data_dir / "summary_statistics.csv")
            print("✅ 데이터 로드 완료")
            print(f"   - 총 실험 횟수: {len(self.results_df)}")
            print(f"   - 요약 통계: {len(self.summary_df)} 조건")
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            
    def analyze_write_buffer_size_impact(self):
        """Write Buffer Size가 성능에 미치는 영향 분석"""
        print("\n" + "="*60)
        print("📊 Write Buffer Size 영향 분석")
        print("="*60)
        
        # 기본 설정 (max_write_buffer_number=2, min_write_buffer_number_to_merge=1)에서의 결과
        baseline_data = self.results_df[
            (self.results_df['max_write_buffer_number'] == 2) & 
            (self.results_df['min_write_buffer_number_to_merge'] == 1)
        ].copy()
        
        # 벤치마크별 분석
        for benchmark in ['fillrandom', 'readrandom', 'overwrite']:
            print(f"\n🔍 {benchmark.upper()} 벤치마크 분석:")
            
            bench_data = baseline_data[baseline_data['benchmark_type'] == benchmark]
            if bench_data.empty:
                continue
                
            # Write buffer size별 평균 지연시간
            latency_by_size = bench_data.groupby('write_buffer_size_mb')['avg_latency_us'].agg(['mean', 'std']).round(3)
            print("\n📈 Write Buffer Size별 평균 지연시간 (μs):")
            print(latency_by_size)
            
            # 최적 성능 찾기
            best_size = latency_by_size['mean'].idxmin()
            worst_size = latency_by_size['mean'].idxmax()
            
            print(f"\n🏆 최적 성능: {best_size}MB (평균 지연시간: {latency_by_size.loc[best_size, 'mean']:.3f}μs)")
            print(f"🔻 최악 성능: {worst_size}MB (평균 지연시간: {latency_by_size.loc[worst_size, 'mean']:.3f}μs)")
            
            # 성능 개선율 계산
            improvement = ((latency_by_size.loc[worst_size, 'mean'] - latency_by_size.loc[best_size, 'mean']) / 
                          latency_by_size.loc[worst_size, 'mean'] * 100)
            print(f"📊 성능 개선율: {improvement:.1f}%")
    
    def analyze_buffer_configuration_impact(self):
        """Buffer 설정 조합이 성능에 미치는 영향 분석"""
        print("\n" + "="*60)
        print("🔧 Buffer 설정 조합 영향 분석")
        print("="*60)
        
        # 128MB에서의 다양한 설정 조합 분석
        config_data = self.results_df[
            (self.results_df['write_buffer_size_mb'] == 128) & 
            (self.results_df['benchmark_type'] == 'fillrandom')
        ].copy()
        
        if config_data.empty:
            print("❌ 128MB 설정 데이터가 없습니다.")
            return
            
        # 설정별 평균 지연시간
        config_analysis = config_data.groupby(['max_write_buffer_number', 'min_write_buffer_number_to_merge'])['avg_latency_us'].agg(['mean', 'std', 'count']).round(3)
        
        print("\n📊 Buffer 설정별 성능 (fillrandom, 128MB):")
        print("max_buffers | min_merge | 평균지연시간(μs) | 표준편차 | 실험횟수")
        print("-" * 65)
        
        for (max_buf, min_merge), stats in config_analysis.iterrows():
            print(f"     {max_buf:2d}     |    {min_merge:2d}    |    {stats['mean']:8.3f}    |  {stats['std']:6.3f}  |    {stats['count']:2.0f}")
        
        # 이상치 탐지 (지연시간이 급격히 증가하는 경우)
        print("\n⚠️  성능 이상치 탐지:")
        high_latency = config_analysis[config_analysis['mean'] > 10.0]  # 10μs 이상
        if not high_latency.empty:
            for (max_buf, min_merge), stats in high_latency.iterrows():
                print(f"   - max_buffers={max_buf}, min_merge={min_merge}: {stats['mean']:.1f}μs (정상 대비 {stats['mean']/2.6:.0f}배)")
        else:
            print("   - 이상치 없음 (모든 설정이 정상 범위)")
    
    def identify_performance_anomalies(self):
        """성능 이상 현상 식별 및 분석"""
        print("\n" + "="*60)
        print("🚨 성능 이상 현상 분석")
        print("="*60)
        
        # 지연시간이 비정상적으로 높은 경우 찾기
        normal_latency_threshold = 10.0  # 10μs를 임계값으로 설정
        anomalies = self.results_df[self.results_df['avg_latency_us'] > normal_latency_threshold]
        
        if anomalies.empty:
            print("✅ 성능 이상 현상 없음")
            return
            
        print(f"🔍 발견된 이상 현상: {len(anomalies)}건")
        
        # 이상 현상 패턴 분석
        anomaly_patterns = anomalies.groupby(['benchmark_type', 'write_buffer_size_mb', 'max_write_buffer_number', 'min_write_buffer_number_to_merge'])['avg_latency_us'].agg(['mean', 'count']).round(1)
        
        print("\n📋 이상 현상 패턴:")
        for (bench, size, max_buf, min_merge), stats in anomaly_patterns.iterrows():
            print(f"   - {bench} | {size}MB | max_buf={max_buf} | min_merge={min_merge}")
            print(f"     평균 지연시간: {stats['mean']:.1f}μs (발생 횟수: {stats['count']:.0f})")
        
        # 가능한 원인 분석
        print("\n🔬 원인 분석:")
        
        # 1. 큰 write_buffer_size와 관련된 이상
        large_buffer_anomalies = anomalies[anomalies['write_buffer_size_mb'] >= 512]
        if not large_buffer_anomalies.empty:
            print("   1️⃣ 큰 Write Buffer Size (≥512MB) 관련:")
            print("      - 메모리 부족으로 인한 스왑 발생 가능성")
            print("      - 컴팩션 지연으로 인한 성능 저하")
        
        # 2. min_write_buffer_number_to_merge=3과 관련된 이상
        merge_anomalies = anomalies[anomalies['min_write_buffer_number_to_merge'] == 3]
        if not merge_anomalies.empty:
            print("   2️⃣ min_write_buffer_number_to_merge=3 관련:")
            print("      - 과도한 버퍼 누적으로 인한 메모리 압박")
            print("      - 대량 컴팩션 작업으로 인한 I/O 병목")
    
    def generate_recommendations(self):
        """실험 결과 기반 최적화 권장사항 생성"""
        print("\n" + "="*60)
        print("💡 최적화 권장사항")
        print("="*60)
        
        # 기본 설정에서의 최적 write_buffer_size 찾기
        baseline_summary = self.summary_df[
            (self.summary_df['max_write_buffer_number'] == 2) & 
            (self.summary_df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        recommendations = []
        
        for benchmark in ['fillrandom', 'readrandom', 'overwrite']:
            bench_data = baseline_summary[baseline_summary['benchmark_type'] == benchmark]
            if not bench_data.empty:
                optimal_size = bench_data.loc[bench_data['avg_latency_us_mean'].idxmin(), 'write_buffer_size_mb']
                optimal_latency = bench_data['avg_latency_us_mean'].min()
                recommendations.append((benchmark, optimal_size, optimal_latency))
        
        print("\n🎯 벤치마크별 최적 설정:")
        for benchmark, size, latency in recommendations:
            print(f"   - {benchmark:12s}: write_buffer_size = {size:3.0f}MB (지연시간: {latency:.3f}μs)")
        
        # 일반적인 권장사항
        print("\n📋 일반 권장사항:")
        print("   1️⃣ Write Buffer Size:")
        print("      - 대부분의 워크로드에서 128MB~256MB가 최적")
        print("      - 512MB 이상은 메모리 부족 시 성능 저하 위험")
        
        print("\n   2️⃣ Buffer 개수 설정:")
        print("      - max_write_buffer_number = 2~4 권장")
        print("      - min_write_buffer_number_to_merge = 1~2 권장")
        print("      - min_merge = 3은 성능 저하 위험 (컴팩션 지연)")
        
        print("\n   3️⃣ 메모리 고려사항:")
        print("      - 총 메모리 사용량 = write_buffer_size × max_write_buffer_number")
        print("      - 시스템 메모리의 25% 이하로 제한 권장")
        
        print("\n   4️⃣ 워크로드별 최적화:")
        print("      - 쓰기 집약적: 128MB, max_buffers=4")
        print("      - 읽기 집약적: 64MB~128MB, max_buffers=2")
        print("      - 혼합 워크로드: 128MB, max_buffers=2")
    
    def create_visualizations(self):
        """실험 결과 시각화"""
        print("\n" + "="*60)
        print("📊 결과 시각화 생성 중...")
        print("="*60)
        
        # 그래프 스타일 설정
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('RocksDB Write Buffer 최적화 실험 결과', fontsize=16, fontweight='bold')
        
        # 1. Write Buffer Size별 지연시간 (기본 설정)
        baseline_data = self.results_df[
            (self.results_df['max_write_buffer_number'] == 2) & 
            (self.results_df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        ax1 = axes[0, 0]
        for benchmark in ['fillrandom', 'readrandom', 'overwrite']:
            bench_data = baseline_data[baseline_data['benchmark_type'] == benchmark]
            if not bench_data.empty:
                latency_stats = bench_data.groupby('write_buffer_size_mb')['avg_latency_us'].agg(['mean', 'std'])
                ax1.errorbar(latency_stats.index, latency_stats['mean'], 
                           yerr=latency_stats['std'], marker='o', label=benchmark, linewidth=2)
        
        ax1.set_xlabel('Write Buffer Size (MB)')
        ax1.set_ylabel('평균 지연시간 (μs)')
        ax1.set_title('Write Buffer Size별 성능 비교')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')  # 로그 스케일로 이상치 표시
        
        # 2. Buffer 설정 조합별 성능 (fillrandom, 128MB)
        ax2 = axes[0, 1]
        config_data = self.results_df[
            (self.results_df['write_buffer_size_mb'] == 128) & 
            (self.results_df['benchmark_type'] == 'fillrandom')
        ]
        
        if not config_data.empty:
            pivot_data = config_data.pivot_table(
                values='avg_latency_us', 
                index='max_write_buffer_number', 
                columns='min_write_buffer_number_to_merge', 
                aggfunc='mean'
            )
            
            sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax2)
            ax2.set_title('Buffer 설정 조합별 지연시간\n(fillrandom, 128MB)')
            ax2.set_xlabel('min_write_buffer_number_to_merge')
            ax2.set_ylabel('max_write_buffer_number')
        
        # 3. 벤치마크별 성능 분포
        ax3 = axes[1, 0]
        normal_data = self.results_df[self.results_df['avg_latency_us'] <= 10.0]  # 정상 범위만
        
        benchmark_order = ['fillrandom', 'readrandom', 'overwrite']
        box_data = [normal_data[normal_data['benchmark_type'] == b]['avg_latency_us'].values 
                   for b in benchmark_order if not normal_data[normal_data['benchmark_type'] == b].empty]
        
        if box_data:
            ax3.boxplot(box_data, labels=benchmark_order[:len(box_data)])
            ax3.set_ylabel('지연시간 (μs)')
            ax3.set_title('벤치마크별 성능 분포 (정상 범위)')
            ax3.grid(True, alpha=0.3)
        
        # 4. 이상치 분석
        ax4 = axes[1, 1]
        anomaly_data = self.results_df[self.results_df['avg_latency_us'] > 10.0]
        
        if not anomaly_data.empty:
            scatter_data = anomaly_data.groupby(['write_buffer_size_mb', 'benchmark_type'])['avg_latency_us'].mean().reset_index()
            
            for benchmark in scatter_data['benchmark_type'].unique():
                bench_scatter = scatter_data[scatter_data['benchmark_type'] == benchmark]
                ax4.scatter(bench_scatter['write_buffer_size_mb'], bench_scatter['avg_latency_us'], 
                          label=benchmark, s=100, alpha=0.7)
            
            ax4.set_xlabel('Write Buffer Size (MB)')
            ax4.set_ylabel('평균 지연시간 (μs)')
            ax4.set_title('성능 이상치 분석')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, '이상치 없음', ha='center', va='center', transform=ax4.transAxes, fontsize=14)
            ax4.set_title('성능 이상치 분석')
        
        plt.tight_layout()
        
        # 그래프 저장
        output_path = self.data_dir / "performance_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📈 시각화 결과 저장: {output_path}")
        
        # 추가 상세 분석 그래프
        self._create_detailed_charts()
        
        plt.show()
    
    def _create_detailed_charts(self):
        """상세 분석 차트 생성"""
        # Write Buffer Size별 상세 분석
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Write Buffer Size 상세 분석', fontsize=16, fontweight='bold')
        
        baseline_data = self.results_df[
            (self.results_df['max_write_buffer_number'] == 2) & 
            (self.results_df['min_write_buffer_number_to_merge'] == 1)
        ]
        
        benchmarks = ['fillrandom', 'readrandom', 'overwrite']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        for i, (benchmark, color) in enumerate(zip(benchmarks, colors)):
            ax = axes[i]
            bench_data = baseline_data[baseline_data['benchmark_type'] == benchmark]
            
            if not bench_data.empty:
                # 개별 데이터 포인트
                for size in bench_data['write_buffer_size_mb'].unique():
                    size_data = bench_data[bench_data['write_buffer_size_mb'] == size]['avg_latency_us']
                    ax.scatter([size] * len(size_data), size_data, alpha=0.6, color=color, s=30)
                
                # 평균선
                latency_stats = bench_data.groupby('write_buffer_size_mb')['avg_latency_us'].mean()
                ax.plot(latency_stats.index, latency_stats.values, 'o-', color=color, linewidth=2, markersize=8)
            
            ax.set_xlabel('Write Buffer Size (MB)')
            ax.set_ylabel('지연시간 (μs)')
            ax.set_title(f'{benchmark.upper()}')
            ax.grid(True, alpha=0.3)
            
            # 이상치가 있는 경우 로그 스케일 적용
            if bench_data['avg_latency_us'].max() > 50:
                ax.set_yscale('log')
        
        plt.tight_layout()
        
        # 상세 분석 그래프 저장
        output_path = self.data_dir / "detailed_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 상세 분석 저장: {output_path}")
    
    def generate_report(self):
        """종합 분석 보고서 생성"""
        print("\n" + "="*60)
        print("📝 종합 분석 보고서 생성")
        print("="*60)
        
        report_path = self.data_dir / "analysis_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# RocksDB Write Buffer 최적화 실험 분석 보고서\n\n")
            f.write("## 실험 개요\n")
            f.write(f"- 총 실험 횟수: {len(self.results_df)}\n")
            f.write(f"- 테스트된 설정 조합: {len(self.summary_df)}\n")
            f.write("- 벤치마크: fillrandom, readrandom, overwrite\n")
            f.write("- Write Buffer Size: 16MB, 64MB, 128MB, 256MB, 512MB\n\n")
            
            # 주요 발견사항
            f.write("## 주요 발견사항\n\n")
            
            # 최적 성능 설정
            baseline_summary = self.summary_df[
                (self.summary_df['max_write_buffer_number'] == 2) & 
                (self.summary_df['min_write_buffer_number_to_merge'] == 1)
            ]
            
            f.write("### 1. 최적 Write Buffer Size\n")
            for benchmark in ['fillrandom', 'readrandom', 'overwrite']:
                bench_data = baseline_summary[baseline_summary['benchmark_type'] == benchmark]
                if not bench_data.empty:
                    optimal_size = bench_data.loc[bench_data['avg_latency_us_mean'].idxmin(), 'write_buffer_size_mb']
                    optimal_latency = bench_data['avg_latency_us_mean'].min()
                    f.write(f"- **{benchmark}**: {optimal_size:.0f}MB (평균 지연시간: {optimal_latency:.3f}μs)\n")
            
            # 성능 이상 현상
            f.write("\n### 2. 성능 이상 현상\n")
            anomalies = self.results_df[self.results_df['avg_latency_us'] > 10.0]
            if not anomalies.empty:
                f.write(f"- 총 {len(anomalies)}건의 성능 이상 현상 발견\n")
                f.write("- 주요 원인:\n")
                f.write("  - 512MB 이상의 큰 Write Buffer Size\n")
                f.write("  - min_write_buffer_number_to_merge=3 설정\n")
                f.write("  - 메모리 부족으로 인한 스왑 발생 추정\n")
            else:
                f.write("- 성능 이상 현상 없음\n")
            
            # 권장사항
            f.write("\n## 최적화 권장사항\n\n")
            f.write("### 일반적인 설정\n")
            f.write("- **write_buffer_size**: 128MB~256MB\n")
            f.write("- **max_write_buffer_number**: 2~4\n")
            f.write("- **min_write_buffer_number_to_merge**: 1~2\n\n")
            
            f.write("### 워크로드별 최적화\n")
            f.write("- **쓰기 집약적**: write_buffer_size=128MB, max_write_buffer_number=4\n")
            f.write("- **읽기 집약적**: write_buffer_size=64MB~128MB, max_write_buffer_number=2\n")
            f.write("- **혼합 워크로드**: write_buffer_size=128MB, max_write_buffer_number=2\n\n")
            
            f.write("### 주의사항\n")
            f.write("- 512MB 이상의 write_buffer_size는 성능 저하 위험\n")
            f.write("- min_write_buffer_number_to_merge=3은 컴팩션 지연 발생\n")
            f.write("- 총 메모리 사용량이 시스템 메모리의 25%를 초과하지 않도록 주의\n")
        
        print(f"📄 분석 보고서 저장: {report_path}")
    
    def run_complete_analysis(self):
        """전체 분석 실행"""
        print("🚀 RocksDB Write Buffer 최적화 실험 결과 분석 시작")
        print("="*60)
        
        # 각 분석 단계 실행
        self.analyze_write_buffer_size_impact()
        self.analyze_buffer_configuration_impact()
        self.identify_performance_anomalies()
        self.generate_recommendations()
        self.create_visualizations()
        self.generate_report()
        
        print("\n" + "="*60)
        print("✅ 분석 완료!")
        print("📁 생성된 파일:")
        print("   - performance_analysis.png: 종합 성능 분석 차트")
        print("   - detailed_analysis.png: 상세 분석 차트")
        print("   - analysis_report.md: 종합 분석 보고서")
        print("="*60)

if __name__ == "__main__":
    # 분석 실행
    analyzer = RocksDBAnalyzer()
    analyzer.run_complete_analysis() 