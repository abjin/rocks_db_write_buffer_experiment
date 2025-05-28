# RocksDB Write Buffer 벤치마크 연구: 성능 측정과 최적화 가이드라인

## 1. 실험 동기

### 

- RocksDB의 Write Buffer 관련 설정이 데이터베이스 성능에 미치는 영향을 정량적으로 분석
- 메모리 사용량과 성능 간의 트레이드오프 관계 규명
- 실무 환경에서 적용 가능한 워크로드별 최적화 가이드라인 도출



## 2. 실험 가설

### 2.1 주요 가설

#### 가설 1: Write Buffer Size와 성능의 관계
**H1**: `write_buffer_size`가 클수록 처리량이 향상되지만, 메모리 사용량도 선형적으로 증가할 것이다.

- **근거**: 큰 버퍼는 더 많은 데이터를 메모리에 보관하여 디스크 I/O를 줄이지만, 메모리 사용량이 증가함
- **예상 결과**: 16MB → 512MB로 증가 시 처리량 2-3배 향상, 메모리 사용량 32배 증가



#### 가설 2: Write Buffer Number와 성능의 관계
**H2**: `max_write_buffer_number`가 증가할수록 처리량이 향상될 것이다.

- **근거**: 더 많은 버퍼로 병렬 처리 가능
- **예상 결과**: 2개 → 6개로 증가 시 처리량 향상



#### 가설 3: Merge 임계값과 성능의 관계
**H3**: `min_write_buffer_number_to_merge`가 높을수록 compaction 시간이 증가할 것이다.

- **근거**: 더 많은 버퍼를 compaction 해야하므로 오버해드 발생
- **예상 결과**: merge=1 → merge=3 시 지연시간 증가





## 3. 실험 설계

### 3.1 실험 환경



### 3.2 실험 시나리오

#### 시나리오 1: Write Buffer Size 극한 테스트 (5개 실험)
**목표**: `write_buffer_size`의 극한 차이로 성능 영향 분석

**변수 설정**:

```bash
write_buffer_sizes=(8388608 33554432 67108864 268435456 536870912)  # 8MB, 32MB, 64MB, 256MB, 512MB
# 다른 모든 옵션은 기본값 유지
max_write_buffer_number=3  # 기본값 고정
min_write_buffer_number_to_merge=1  # 기본값 고정
```

**테스트**:

- `fillrandom`: 2M 키-값 쌍 (2KB 값 크기)

#### 시나리오 2: Max Write Buffer Number 극한 테스트 (5개 실험)
**목표**: `max_write_buffer_number`의 극한 차이로 병렬성 영향 분석

**변수 설정**:

```bash
write_buffer_size=67108864  # 64MB 고정 (기본값)
max_write_buffer_numbers=(1 2 4 8 16)  # 1개, 2개, 4개, 8개, 16개
min_write_buffer_number_to_merge=1  # 기본값 고정
```

**테스트**:

- `fillrandom`: 2M 키-값 쌍 (2KB 값 크기)

#### 시나리오 3: Min Write Buffer Number To Merge 극한 테스트 (5개 실험)
**목표**: `min_write_buffer_number_to_merge`의 극한 차이로 병합 전략 영향 분석

**변수 설정**:

```bash
write_buffer_size=67108864  # 64MB 고정 (기본값)
max_write_buffer_number=8  # 8개로 증가 (병합 테스트를 위해)
min_write_buffer_number_to_merges=(1 2 4 6 8)  # 1, 2, 4, 6, 8
```

**테스트**:
- `fillrandom`: 2M 키-값 쌍 (2KB 값 크기)

### 3.3 측정 지표

#### 3.3.1 주요 성능 지표
- **Write 처리량**: fillrandom Operations per second (ops/sec)
- **Read 처리량**: readrandom Operations per second (ops/sec)
- **Write 지연시간**: P50, P95, P99 latency (μs)
- **Read 지연시간**: P50, P95, P99 latency (μs)
- **메모리 사용량**: Peak memory usage (MB)

#### 3.3.2 보조 지표
- **Write Amplification**: 쓰기 증폭 비율
- **Read Amplification**: 읽기 증폭 비율
- **Compaction 통계**: 백그라운드 작업 빈도 및 시간
- **SST 파일 수**: LSM Tree 구조 복잡도

#### 3.3.3 Write Buffer 설정이 Read 성능에 미치는 영향
- **작은 Write Buffer**: 빈번한 플러시 → 많은 SST 파일 → Read 성능 저하
- **큰 Write Buffer**: 적은 플러시 → 적은 SST 파일 → Read 성능 향상
- **메모리 경합**: Write Buffer 메모리 사용 ↑ → Block Cache 효율 ↓ → Read 성능 저하


# 4. 실험 결과

## 4.1 상세 분석 문서

### 📊 시나리오별 분석 보고서

#### [시나리오 1: Write Buffer Size 최적화 분석](./write_buffer_experiment/scenario1_analysis.md)
- **실험 범위**: 8MB ~ 512MB (64배 차이)
- **핵심 발견**: 32MB에서 최고 성능 (36% 향상)
- **주요 지표**: Flush 분석, Write Stall, Compaction 부하
- **권장사항**: 워크로드별 최적 설정 가이드

#### [시나리오 2: Max Write Buffer Number 분석](./write_buffer_experiment/scenario2_analysis.md)
- **실험 범위**: 1개 ~ 16개 버퍼
- **핵심 발견**: 병렬성과 메모리 사용량의 트레이드오프
- **주요 지표**: 버퍼 개수별 성능 변화
- **권장사항**: 시스템 리소스 기반 최적화

#### [시나리오 3: Min Write Buffer Number To Merge 분석](./write_buffer_experiment/scenario3_analysis.md)
- **실험 범위**: 1 ~ 8 병합 임계값
- **핵심 발견**: 병합 전략이 Compaction에 미치는 영향
- **주요 지표**: 병합 지연과 I/O 효율성
- **권장사항**: Compaction 최적화 전략

## 4.2 실험 데이터 및 스크립트

### 🔬 실험 자동화
- **실행 스크립트**: [`run_experiments.sh`](./write_buffer_experiment/run_experiments.sh)
- **실험 로그**: [`run.log`](./write_buffer_experiment/run.log)
- **원시 데이터**: [`results/`](./write_buffer_experiment/results/) 폴더

### 📈 주요 성과 요약
- **최적 Write Buffer Size**: 32MB (OLTP 워크로드 기준)
- **성능 향상**: 기본 설정 대비 최대 36% 처리량 증가
- **Write Stall 해결**: 16MB 이상 설정으로 완전 해결
- **메모리 효율성**: 64MB까지 선형적 성능 향상 확인

