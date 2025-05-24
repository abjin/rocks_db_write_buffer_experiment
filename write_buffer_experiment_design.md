# RocksDB Write Buffer 최적화 실험 설계서

## 📋 실험 개요

### 실험 제목
**RocksDB Write Buffer 최적화: 성능과 메모리 사용량의 트레이드오프 분석**

### 실험 목적
- RocksDB의 Write Buffer 관련 설정이 데이터베이스 성능에 미치는 영향을 정량적으로 분석
- 메모리 사용량과 성능 간의 트레이드오프 관계 규명
- 실무 환경에서 적용 가능한 최적화 가이드라인 도출

### 연구 배경
RocksDB는 LSM-tree 기반의 key-value 저장소로, Write Buffer(MemTable)는 쓰기 성능에 직접적인 영향을 미치는 핵심 구성요소입니다. Write Buffer의 크기와 관리 정책은 다음과 같은 측면에서 성능에 영향을 줍니다:

- **메모리 사용량**: 더 큰 버퍼는 더 많은 메모리를 사용
- **Flush 빈도**: 버퍼 크기가 클수록 디스크로의 Flush 빈도 감소
- **Write Amplification**: 버퍼 크기와 compaction 정책에 따라 쓰기 증폭 변화
- **읽기 성능**: 메모리 내 데이터 비율이 읽기 성능에 영향

---

## 🎯 연구 가설

### 주 가설 (H1)
**"Write Buffer 크기가 클수록 쓰기 성능이 향상될 것이다"**

**근거**: 
- 큰 버퍼는 더 많은 데이터를 메모리에 유지
- Flush 빈도 감소로 I/O 오버헤드 줄어듦
- Write amplification 감소 예상

### 부 가설 (H2)
**"메모리 사용량과 성능 간에는 선형적 관계가 존재할 것이다"**

**근거**:
- 메모리 투입량에 비례한 성능 향상 기대
- 캐시 효과로 인한 읽기 성능 개선

### 대립 가설 (H3)
**"특정 임계점 이후에는 성능 향상이 둔화되거나 오히려 저하될 것이다"**

**근거**:
- 메모리 할당 오버헤드 증가
- GC 압박 또는 시스템 리소스 경합
- Cache locality 악화 가능성

---

## 🔬 실험 설계

### 1. 실험 방법론

#### 1.1 실험 타입
- **통제된 벤치마크 실험** (Controlled Benchmark Experiment)
- **반복 측정 설계** (Repeated Measures Design)
- **요인 분석** (Factorial Analysis)

#### 1.2 통제 변수
- **하드웨어 환경**: 동일한 서버/VM 사용
- **운영체제**: 동일한 OS 및 커널 버전
- **RocksDB 버전**: 동일한 빌드 사용
- **데이터 크기**: 고정된 키-값 쌍 수와 크기
- **측정 시점**: 동일한 조건에서 측정

#### 1.3 독립 변수 (Independent Variables)

| 변수명 | 설명 | 값 범위 | 단위 |
|--------|------|---------|------|
| `write_buffer_size` | MemTable 크기 | 16, 64, 128, 256, 512 | MB |
| `max_write_buffer_number` | 최대 MemTable 개수 | 2, 4, 6 | 개 |
| `min_write_buffer_number_to_merge` | 병합할 최소 MemTable 수 | 1, 2, 3 | 개 |

#### 1.4 종속 변수 (Dependent Variables)

| 지표 | 설명 | 단위 | 중요도 |
|------|------|------|--------|
| **Throughput** | 초당 처리 작업 수 | ops/sec | 높음 |
| **P99 Latency** | 99% 구간 응답 시간 | μs | 높음 |
| **Average Latency** | 평균 응답 시간 | μs | 중간 |
| **Write Amplification** | 쓰기 증폭 계수 | 배수 | 높음 |
| **Memory Usage** | 메모리 사용량 | MB | 중간 |
| **Compaction Frequency** | Compaction 발생 빈도 | 횟수/분 | 낮음 |

---

## 📊 실험 시나리오

### 시나리오 1: 기본 Write Buffer Size 영향 분석

**목적**: Write Buffer 크기가 성능에 미치는 기본적인 영향 파악

**설정**:
- `max_write_buffer_number`: 2 (고정)
- `min_write_buffer_number_to_merge`: 1 (고정)
- `write_buffer_size`: 16MB → 64MB → 128MB → 256MB → 512MB

**벤치마크 타입**:
- `fillrandom`: 순차적 랜덤 키 삽입
- `readrandom`: 랜덤 키 읽기
- `overwrite`: 기존 키 덮어쓰기

**반복 횟수**: 각 설정당 3회

### 시나리오 2: 버퍼 개수와 병합 정책 최적화

**목적**: 최적 Buffer Size에서 다른 파라미터들의 영향 분석

**설정**:
- `write_buffer_size`: 128MB (시나리오 1 결과 기준)
- `max_write_buffer_number`: 2, 4, 6
- `min_write_buffer_number_to_merge`: 1, 2, 3

**조합**: 3 × 3 = 9가지 조합

**벤치마크 타입**: `fillrandom` (가장 중요한 쓰기 성능 측정)

### 시나리오 3: 메모리 효율성 분석

**목적**: 단위 메모리당 성능 효율성 측정

**계산식**:
```
Total Memory = write_buffer_size × max_write_buffer_number
Memory Efficiency = Throughput / Total Memory
```

**분석 관점**:
- 메모리 투자 대비 성능 향상
- 최적 ROI(Return on Investment) 지점 찾기

---

## 🛠️ 실험 환경 및 도구

### 1. 하드웨어 요구사항
- **CPU**: 최소 4코어 (8코어 권장)
- **메모리**: 최소 8GB (16GB 권장)
- **스토리지**: SSD 권장 (최소 100GB 여유공간)

### 2. 소프트웨어 스택
- **OS**: Linux/macOS
- **RocksDB**: 최신 버전
- **벤치마크 도구**: db_bench
- **모니터링**: iostat, htop, custom monitoring
- **분석**: Python (pandas, matplotlib, seaborn)

### 3. 실험 자동화
```bash
# 실험 실행
./run_write_buffer_experiment.sh

# 결과 분석
python3 analyze_results.py
```

---

## 📈 데이터 수집 및 측정

### 1. 성능 메트릭 수집

#### Primary Metrics (db_bench 출력)
```bash
# 처리량 추출
grep "ops/sec" result.txt

# 지연시간 분포 추출  
grep "Percentiles:" result.txt

# Write amplification 추출
grep "Write amplification:" result.txt
```

#### Secondary Metrics (시스템 모니터링)
```bash
# CPU 사용률
top -bn1 | grep "Cpu(s)"

# 메모리 사용량
free -m

# I/O 통계
iostat -d 1 1
```

### 2. 데이터 정규화 및 검증

#### 이상치 처리
- **Z-score > 3**: 이상치로 간주하여 제외
- **반복 측정**: 최소 3회 반복으로 안정성 확보

#### 통계적 유의성
- **평균 및 표준편차** 계산
- **신뢰구간** 95% 수준으로 설정

---

## 🎯 예상 결과 및 분석 계획

### 1. 예상 결과 패턴

#### Pattern A: 선형 증가 (H1 지지)
```
성능 ∝ write_buffer_size
16MB < 64MB < 128MB < 256MB < 512MB
```

#### Pattern B: 최적점 존재 (H3 지지)
```
성능: 16MB < 64MB < 128MB > 256MB > 512MB
최적점: 128MB
```

#### Pattern C: 포화 곡선
```
성능: 16MB << 64MB ≈ 128MB ≈ 256MB ≈ 512MB
포화점: 64MB 이후
```

### 2. 심화 분석 방향

#### 원인 분석
- **메모리 할당 오버헤드** 측정
- **Compaction 빈도** 분석
- **Cache miss rate** 조사

#### 워크로드별 특성
- **Write-heavy**: `fillrandom`, `overwrite`
- **Read-heavy**: `readrandom`
- **Mixed workload**: 향후 확장 가능

---

## 📊 결과 시각화 계획

### 1. 핵심 그래프

#### 그래프 1: Buffer Size Impact
```python
# X축: write_buffer_size (MB)
# Y축: throughput (ops/sec)
# 보조축: P99 latency (μs)
```

#### 그래프 2: Memory Efficiency
```python
# X축: total_memory_usage (MB)
# Y축: throughput (ops/sec) 
# 버블크기: memory_efficiency
```

#### 그래프 3: Parameter Combination Heatmap
```python
# X축: max_write_buffer_number
# Y축: min_write_buffer_number_to_merge
# 색상: throughput
```

### 2. 통계 테이블

#### 요약 통계
| Buffer Size | Throughput (평균) | P99 Latency (평균) | Std Dev | 95% CI |
|-------------|-------------------|-------------------|---------|---------|
| 16MB | XXX,XXX ops/sec | XX.X μs | XX | [XX, XX] |
| ... | ... | ... | ... | ... |

---

## 🔍 품질 보증 및 재현성

### 1. 실험 재현성 확보

#### 환경 문서화
```bash
# 시스템 정보 수집
uname -a > system_info.txt
lscpu >> system_info.txt
free -h >> system_info.txt
```

#### 설정 버전 관리
- 모든 실험 설정을 Git으로 관리
- 실험 실행 시 commit hash 기록

### 2. 데이터 검증

#### Sanity Check
- **기본 상식 검증**: 더 많은 메모리 = 더 나은 성능 (일반적으로)
- **일관성 검증**: 동일 설정 반복 실험 간 편차 < 5%

#### Cross-validation
- **다른 워크로드**로 검증
- **다른 하드웨어**에서 추가 실험

---

## 📝 15분 발표 스토리라인

### 1단계: 문제 제기 (2분)
- "메모리를 늘리면 성능이 좋아질까?"
- 실제 운영 환경에서의 딜레마
- 연구 질문 명확화

### 2단계: 과학적 접근 (3분)
- 가설 수립 과정
- 실험 설계의 타당성
- 측정 지표의 중요성

### 3단계: 데이터 스토리텔링 (5분)
- "예상과 다른 결과가 나왔습니다"
- 시각화로 보는 성능 변화
- 숨겨진 패턴 발견

### 4단계: 통찰과 해석 (4분)
- 왜 이런 결과가 나왔을까?
- 이론과 실제의 차이
- 실무진들을 위한 가이드라인

### 5단계: 마무리 (1분)
- 핵심 메시지
- 후속 연구 방향
- 실무 적용 방안

---

## ⚠️ 제한사항 및 고려사항

### 실험 제한사항
- **단일 하드웨어 환경**: 일반화 한계
- **특정 워크로드**: 실제 애플리케이션과 차이
- **제한된 측정 기간**: 장기 영향 미반영

### 위험 요소 관리
- **시스템 리소스 고갈**: 모니터링으로 사전 감지
- **데이터 손실**: 백업 및 복구 계획
- **실험 중단**: 체크포인트 기능

### 향후 확장 방향
- **다양한 워크로드** 패턴 실험
- **클러스터 환경**에서의 검증
- **실시간 워크로드** 적용 실험

---

## 📚 참고문헌 및 리소스

### 기술 문서
- [RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide)
- [Memory usage in RocksDB](https://github.com/facebook/rocksdb/wiki/Memory-usage-in-RocksDB)
- [Write Buffer Manager](https://github.com/facebook/rocksdb/wiki/Write-Buffer-Manager)

### 학술 자료
- "LSM-trees: A Survey" (Chen et al., 2021)
- "Performance Analysis of LSM-trees" (O'Neil et al., 1996)

### 실습 리소스
- [db_bench Guide](https://github.com/facebook/rocksdb/wiki/Benchmarking-tools)
- [RocksDB Examples](https://github.com/facebook/rocksdb/tree/main/examples)

---

*이 문서는 RocksDB Write Buffer 최적화 실험의 체계적인 설계와 실행을 위한 완전한 가이드입니다.* 