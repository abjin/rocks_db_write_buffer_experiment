# RocksDB Write Buffer 최적화 실험

## 📖 실험 개요
RocksDB의 Write Buffer 관련 설정이 성능에 미치는 영향을 체계적으로 분석하는 실험입니다.

### 🎯 실험 목표
- `write_buffer_size`, `max_write_buffer_number`, `min_write_buffer_number_to_merge` 설정 최적화
- 메모리 사용량 대비 성능 효율성 분석
- 실무 적용 가능한 설정 가이드라인 도출

### 📋 상세 실험 설계
자세한 실험 설계 및 방법론은 다음 문서를 참조하세요:
**[📄 Write Buffer 최적화 실험 설계서](write_buffer_experiment_design.md)**

## 🛠️ 실험 환경 설정

### 1. RocksDB 빌드
```bash
# RocksDB 클론 및 빌드
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
make db_bench

# db_bench 경로 확인
ls -la db_bench
```

### 2. Python 환경 설정
```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 3. 실험 스크립트 권한 설정
```bash
chmod +x run_write_buffer_experiment.sh
```

## 🚀 실험 실행

### 전체 실험 실행
```bash
# db_bench 경로 수정 (필요시)
# run_write_buffer_experiment.sh 파일의 DB_BENCH_PATH 변수 수정

# 실험 실행
./run_write_buffer_experiment.sh
```

### 실험 설정 커스터마이징
스크립트 내 다음 변수들을 수정하여 실험을 조정할 수 있습니다:

```bash
# 실험 설정
NUM_KEYS=1000000           # 실험용 키 개수
NUM_ITERATIONS=3           # 반복 실험 횟수
VALUE_SIZE=1024           # 값 크기 (bytes)

# Write Buffer 크기 (bytes)
WRITE_BUFFER_SIZES=("16777216" "67108864" "134217728" "268435456" "536870912")

# 최대 버퍼 개수
MAX_WRITE_BUFFER_NUMBERS=("2" "4" "6")

# 병합할 최소 버퍼 개수
MIN_WRITE_BUFFER_NUMBER_TO_MERGE=("1" "2" "3")
```

## 📊 결과 분석

### 자동 분석
실험 완료 후 Python 분석 스크립트가 자동으로 실행됩니다:

```bash
# 수동으로 분석 실행하려면
python3 analyze_results.py
```

### 생성되는 결과물
```
write_buffer_experiment/
├── results/           # 원시 실험 결과
├── logs/             # 시스템 모니터링 로그
└── analysis/         # 분석 결과
    ├── experiment_results.csv
    ├── summary_statistics.csv
    ├── experiment_report.md
    └── *.png         # 시각화 그래프들
```

## 📈 분석 결과

### 1. 주요 시각화
- **write_buffer_size_impact.png**: Buffer 크기 영향 분석
- **latency_analysis.png**: 지연시간 분석
- **memory_efficiency.png**: 메모리 효율성 분석
- **optimal_combination.png**: 최적 조합 비교

### 2. 핵심 지표
- **Throughput**: 초당 처리 작업 수 (ops/sec)
- **P99 Latency**: 99% 구간 지연시간 (μs)
- **Write Amplification**: 쓰기 증폭 계수
- **Memory Efficiency**: MB당 처리량

## 🎯 예상 결과

### 가설
1. Write buffer 크기가 클수록 성능이 향상될 것
2. 메모리 사용량과 성능 간 선형 관계 존재

### 실제 예상되는 발견
- 특정 크기(~128MB)에서 성능 최적점 존재
- 과도한 버퍼 크기에서 성능 저하 발생
- 메모리 효율성과 절대 성능 간 트레이드오프

## 🔧 문제 해결

### db_bench를 찾을 수 없는 경우
```bash
# RocksDB 빌드 확인
cd rocksdb
make clean && make db_bench

# 절대 경로로 설정
DB_BENCH_PATH="/absolute/path/to/rocksdb/db_bench"
```

### Python 패키지 오류
```bash
# 업그레이드
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### 메모리 부족 오류
```bash
# 실험 규모 조정
NUM_KEYS=100000        # 키 개수 감소
VALUE_SIZE=512         # 값 크기 감소
```

## 📝 15분 발표 구성

### 발표 구조 (총 15분)
1. **동기 및 배경** (2분)
   - 실험 동기
   - 기존 이론
   - 연구 질문

2. **가설 및 실험 설계** (3분)
   - 가설 설정
   - 실험 방법론
   - 측정 지표

3. **실험 결과** (5분)
   - 데이터 시각화
   - 주요 발견사항
   - 예상외 결과

4. **결과 분석 및 해석** (4분)
   - 원인 분석
   - 이론과 실제 차이
   - 최적화 포인트

5. **결론 및 향후 과제** (1분)
   - 핵심 인사이트
   - 실무 적용 방안

## 📞 지원

실험 중 문제가 발생하면:
1. 로그 파일 확인: `write_buffer_experiment/logs/`
2. 시스템 리소스 확인: `htop`, `free -h`
3. db_bench 매뉴얼 참조: `./db_bench --help`

## 📚 참고 자료
- **[📄 실험 설계 문서](write_buffer_experiment_design.md)** - 상세한 실험 방법론 및 가설
- [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki)
- [RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide)
- [db_bench Guide](https://github.com/facebook/rocksdb/wiki/Benchmarking-tools)
