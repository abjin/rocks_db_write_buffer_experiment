# RocksDB Write Buffer 최적화: 성능과 메모리 사용량의 트레이드오프 분석

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



### 3.2 실험 시나리오 (단일 옵션 변경)

#### 시나리오 1: Write Buffer Size 단독 테스트
**목표**: `write_buffer_size`만 변경하여 성능 영향 분석

**변수 설정**:

```bash
write_buffer_sizes=(67108864 134217728 268435456)  # 64MB, 128MB, 256MB
# 다른 모든 옵션은 기본값 유지
max_write_buffer_number=3  # 기본값 고정
min_write_buffer_number_to_merge=1  # 기본값 고정
```

**테스트**:

- `fillrandom`: 1M 키-값 쌍

#### 시나리오 2: Max Write Buffer Number 단독 테스트
**목표**: `max_write_buffer_number`만 변경하여 성능 영향 분석

**변수 설정**:

```bash
write_buffer_size=67108864  # 64MB 고정 (기본값)
max_write_buffer_numbers=(2 4 6)  # 변경 대상
min_write_buffer_number_to_merge=1  # 기본값 고정
```

**테스트**:

- `fillrandom`: 동일 조건

#### 시나리오 3: Min Write Buffer Number To Merge 단독 테스트
**목표**: `min_write_buffer_number_to_merge`만 변경하여 성능 영향 분석

**변수 설정**:

```bash
write_buffer_size=67108864  # 64MB 고정 (기본값)
max_write_buffer_number=3  # 기본값 고정
min_write_buffer_number_to_merges=(1 2 3)  # 변경 대상
```

**테스트**:
- `fillrandom`: 동일 조건

### 3.3 측정 지표

#### 3.3.1 주요 성능 지표
- **처리량**: Operations per second (ops/sec)
- **지연시간**: P99 latency (μs)
- **메모리 사용량**: Peak memory usage (MB)

#### 3.3.2 보조 지표
- **Write Amplification**: 쓰기 증폭 비율
- **Compaction 빈도**: 백그라운드 작업 횟수
