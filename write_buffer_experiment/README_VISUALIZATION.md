# RocksDB Write Buffer Size 최적화 실험 - 시각화 도구

## 📊 개요

이 디렉토리에는 RocksDB Write Buffer Size 최적화 실험 결과를 시각화하는 도구들이 포함되어 있습니다.

## 🎯 생성된 그래프

### 1. 시나리오 1 분석 결과
- **scenario1_analysis_charts.png**: 9개의 종합 성능 차트
  - Write 처리량 분석
  - 상대적 성능 비교
  - 지연시간 분석 (로그 스케일)
  - Write Amplification 트렌드
  - Compaction 부하 분석
  - Write Stall 발생 시간
  - 처리량 vs 메모리 사용량 트레이드오프
  - 종합 성능 점수
  - 실무 적용 권장사항

- **scenario1_summary_table.png**: 핵심 지표 요약 테이블

## 🛠️ 사용 가능한 스크립트

### 1. 시각화 생성 스크립트
```bash
# 영어 버전 (권장)
python3 visualize_scenario1_en.py

# 한글 버전 (폰트 문제 가능성)
python3 visualize_scenario1.py
```

### 2. 그래프 뷰어
```bash
python3 view_graphs.py
```

## 📈 주요 발견사항

### 🎯 최적 설정: 32MB Write Buffer Size
- **성능 향상**: 기본 8MB 대비 36% 처리량 증가 (49,841 ops/sec)
- **지연시간**: P99 244μs로 가장 낮은 지연시간
- **안정성**: Write Stall 완전 해결

### ⚠️ 주의사항
- **16MB 미만**: Write Stall 발생 위험 (절대 금지)
- **512MB 이상**: 성능 향상 없이 메모리만 낭비

### 📊 워크로드별 권장 설정

| 워크로드 유형 | 권장 설정 | 이유 |
|-------------|----------|------|
| 일반 OLTP | 32MB | 최고 처리량 + 낮은 지연시간 |
| 고성능 요구 | 64MB | 높은 처리량 + 낮은 Write Amplification |
| 메모리 제약 | 32MB | 최소 권장 크기 |
| 배치 처리 | 256MB | 낮은 Write Amplification |

## 🔧 필요한 패키지

```bash
pip install matplotlib seaborn pandas numpy
```

## 📁 파일 구조

```
write_buffer_experiment/
├── scenario1_analysis.md              # 분석 보고서
├── visualize_scenario1_en.py          # 영어 시각화 스크립트
├── visualize_scenario1.py             # 한글 시각화 스크립트
├── view_graphs.py                     # 그래프 뷰어
├── scenario1_analysis_charts.png      # 종합 성능 차트
├── scenario1_summary_table.png        # 요약 테이블
└── README_VISUALIZATION.md            # 이 파일
```

## 🚀 빠른 시작

1. **그래프 생성**:
   ```bash
   cd write_buffer_experiment
   python3 visualize_scenario1_en.py
   ```

2. **그래프 확인**:
   ```bash
   python3 view_graphs.py
   ```

3. **파일 확인**:
   ```bash
   ls -la *.png
   ```

## 📊 그래프 해석 가이드

### 1. Write 처리량 차트
- 32MB에서 최고 성능 달성
- 512MB에서 성능 저하 확인

### 2. Write Amplification 트렌드
- 버퍼 크기가 클수록 Write Amplification 감소
- 64MB에서 균형점 (1.56x)

### 3. Write Stall 분석
- 8MB에서만 7.15초의 심각한 Stall 발생
- 32MB 이상에서 완전 해결

### 4. 종합 성능 점수
- 모든 지표를 가중 평균한 종합 점수
- 32MB가 최고 점수 달성

## 💡 실무 적용 팁

1. **시작점**: 32MB로 설정
2. **모니터링**: Write Stall 및 Write Amplification 지속 관찰
3. **튜닝**: 워크로드에 따라 64MB까지 증가 고려
4. **금기사항**: 16MB 미만 설정 절대 금지

## 🔍 추가 분석

더 자세한 분석 내용은 `scenario1_analysis.md` 파일을 참조하세요. 