# RocksDB Write Buffer 최적화 실험 분석 보고서

## 실험 개요
- 총 실험 횟수: 69
- 테스트된 설정 조합: 23
- 벤치마크: fillrandom, readrandom, overwrite
- Write Buffer Size: 16MB, 64MB, 128MB, 256MB, 512MB

## 주요 발견사항

### 1. 최적 Write Buffer Size
- **fillrandom**: 256MB (평균 지연시간: 2.610μs)
- **readrandom**: 512MB (평균 지연시간: 2.660μs)
- **overwrite**: 256MB (평균 지연시간: 2.590μs)

### 2. 성능 이상 현상
- 총 12건의 성능 이상 현상 발견
- 주요 원인:
  - 512MB 이상의 큰 Write Buffer Size
  - min_write_buffer_number_to_merge=3 설정
  - 메모리 부족으로 인한 스왑 발생 추정

## 최적화 권장사항

### 일반적인 설정
- **write_buffer_size**: 128MB~256MB
- **max_write_buffer_number**: 2~4
- **min_write_buffer_number_to_merge**: 1~2

### 워크로드별 최적화
- **쓰기 집약적**: write_buffer_size=128MB, max_write_buffer_number=4
- **읽기 집약적**: write_buffer_size=64MB~128MB, max_write_buffer_number=2
- **혼합 워크로드**: write_buffer_size=128MB, max_write_buffer_number=2

### 주의사항
- 512MB 이상의 write_buffer_size는 성능 저하 위험
- min_write_buffer_number_to_merge=3은 컴팩션 지연 발생
- 총 메모리 사용량이 시스템 메모리의 25%를 초과하지 않도록 주의
