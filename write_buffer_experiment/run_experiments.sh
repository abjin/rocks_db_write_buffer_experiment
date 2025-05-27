#!/bin/bash

# RocksDB Write Buffer 최적화 실험 자동화 스크립트 (개선된 버전)
# 환경: CPU 4코어, 메모리 8.59GB
# 목표: 극명한 성능 차이를 통한 파라미터별 영향 분석

set -e  # 에러 발생 시 스크립트 중단

# =============================================================================
# 실험 환경 설정 (극명한 차이를 위한 개선된 설정)
# =============================================================================

# 기본 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROCKSDB_DIR="$(dirname "$SCRIPT_DIR")"
DB_BENCH="$ROCKSDB_DIR/db_bench"
RESULTS_DIR="$SCRIPT_DIR/results"
DB_PATH="$SCRIPT_DIR/rocksdb_test"

# 결과 디렉토리 생성
mkdir -p "$RESULTS_DIR"

# 실험 공통 설정 (시간 단축을 위한 최적화된 설정)
NUM_KEYS=1000000         # 100만 키-값 쌍 (의미있는 차이 유지하면서 시간 단축)
VALUE_SIZE=2048          # 2KB 값 크기 -> 총 약 2GB 데이터
NUM_THREADS=4            # CPU 코어 수에 맞춤
CACHE_SIZE=268435456     # 256MB 블록 캐시 (메모리 압박 유지)

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$RESULTS_DIR/experiment.log"
}

# 시스템 정보 수집 함수
collect_system_info() {
    local test_name=$1
    local output_file="$RESULTS_DIR/${test_name}_system.txt"
    
    echo "=== System Info for $test_name ===" > "$output_file"
    echo "Timestamp: $(date)" >> "$output_file"
    echo "CPU Info:" >> "$output_file"
    cat /proc/cpuinfo | grep "model name" | head -1 >> "$output_file"
    echo "Memory Info:" >> "$output_file"
    free -h >> "$output_file"
    echo "Disk Info:" >> "$output_file"
    df -h "$SCRIPT_DIR" >> "$output_file"
    echo "" >> "$output_file"
}

# 데이터베이스 초기화 함수
cleanup_db() {
    log "데이터베이스 정리 중..."
    rm -rf "$DB_PATH"
    sync
    sleep 1  # 대기 시간 단축
    # 메모리 캐시 정리 (선택적)
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1 || true
}

# 실험 실행 함수 (성능 측정 강화)
run_experiment() {
    local test_name=$1
    local write_buffer_size=$2
    local max_write_buffer_number=$3
    local min_write_buffer_number_to_merge=$4
    local additional_params=${5:-""}
    
    log "실험 시작: $test_name"
    log "  - write_buffer_size: $(($write_buffer_size / 1024 / 1024))MB"
    log "  - max_write_buffer_number: $max_write_buffer_number"
    log "  - min_write_buffer_number_to_merge: $min_write_buffer_number_to_merge"
    log "  - additional_params: $additional_params"
    
    # 시스템 정보 수집
    collect_system_info "$test_name"
    
    # 데이터베이스 정리
    cleanup_db
    
    # 실험 실행 (더 상세한 측정)
    local output_file="$RESULTS_DIR/${test_name}_result.txt"
    
    # 시작 시간 기록
    local start_time=$(date +%s)
    
    # Write 성능 측정
    "$DB_BENCH" \
        --benchmarks=fillrandom \
        --db="$DB_PATH" \
        --num=$NUM_KEYS \
        --value_size=$VALUE_SIZE \
        --threads=$NUM_THREADS \
        --write_buffer_size=$write_buffer_size \
        --max_write_buffer_number=$max_write_buffer_number \
        --min_write_buffer_number_to_merge=$min_write_buffer_number_to_merge \
        --cache_size=$CACHE_SIZE \
        --bloom_bits=10 \
        --compression_type=snappy \
        --statistics \
        --histogram \
        --report_interval_seconds=5 \
        --stats_interval_seconds=10 \
        --perf_level=2 \
        $additional_params \
        2>&1 | tee "$output_file"

    # Write 완료 후 즉시 Read 성능 측정 (대기시간 단축)
    echo "=== READ PERFORMANCE TEST ===" >> "$output_file"
    log "Read 성능 측정 시작: $test_name"
    
    "$DB_BENCH" \
        --benchmarks=readrandom \
        --db="$DB_PATH" \
        --num=$NUM_KEYS \
        --reads=$((NUM_KEYS / 4)) \
        --threads=$NUM_THREADS \
        --cache_size=$CACHE_SIZE \
        --bloom_bits=10 \
        --compression_type=snappy \
        --statistics \
        --histogram \
        --report_interval_seconds=10 \
        --use_existing_db=true \
        2>&1 | tee -a "$output_file"
    
    # 종료 시간 기록
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Total experiment duration: ${duration} seconds" >> "$output_file"
    log "실험 완료: $test_name (소요시간: ${duration}초)"
    echo "----------------------------------------"
    
    # 실험 간 안정화 대기 (30초로 단축)
    log "시스템 안정화를 위해 30초 대기 중..."
    sleep 30
}

# =============================================================================
# 실험 시작
# =============================================================================

log "RocksDB Write Buffer 최적화 실험 시작 (개선된 버전)"
log "환경: CPU 4코어, 메모리 8.59GB"
log "키-값 쌍 수: $NUM_KEYS, 값 크기: ${VALUE_SIZE}B, 스레드 수: $NUM_THREADS"
log "예상 총 데이터 크기: $(($NUM_KEYS * $VALUE_SIZE / 1024 / 1024 / 1024))GB"

# =============================================================================
# 시나리오 1: Write Buffer Size 극한 테스트 (5개 실험)
# =============================================================================

log "=== 시나리오 1: Write Buffer Size 극한 테스트 ==="

# 실험 1-1: 8MB Write Buffer (매우 작음 - 빈번한 플러시)
run_experiment "scenario1_8mb_extreme_small" \
    8388608 \
    3 \
    1

# 실험 1-2: 32MB Write Buffer (작음)
run_experiment "scenario1_32mb_small" \
    33554432 \
    3 \
    1

# 실험 1-3: 64MB Write Buffer (기본값)
run_experiment "scenario1_64mb_default" \
    67108864 \
    3 \
    1

# 실험 1-4: 256MB Write Buffer (큼 - 메모리 압박)
run_experiment "scenario1_256mb_large" \
    268435456 \
    3 \
    1

# 실험 1-5: 512MB Write Buffer (매우 큼 - 극한 메모리 사용)
run_experiment "scenario1_512mb_extreme_large" \
    536870912 \
    3 \
    1

# =============================================================================
# 시나리오 2: Max Write Buffer Number 극한 테스트 (5개 실험)
# =============================================================================

log "=== 시나리오 2: Max Write Buffer Number 극한 테스트 ==="

# 실험 2-1: 1개 Write Buffer (최소 - 병목 발생)
run_experiment "scenario2_1buffer_bottleneck" \
    67108864 \
    1 \
    1

# 실험 2-2: 2개 Write Buffer (적음)
run_experiment "scenario2_2buffers_low" \
    67108864 \
    2 \
    1

# 실험 2-3: 4개 Write Buffer (CPU 코어 수와 동일)
run_experiment "scenario2_4buffers_optimal" \
    67108864 \
    4 \
    1

# 실험 2-4: 8개 Write Buffer (많음 - 메모리 사용량 증가)
run_experiment "scenario2_8buffers_high" \
    67108864 \
    8 \
    1

# 실험 2-5: 16개 Write Buffer (매우 많음 - 극한 메모리 사용)
run_experiment "scenario2_16buffers_extreme" \
    67108864 \
    16 \
    1

# =============================================================================
# 시나리오 3: Min Write Buffer Number To Merge 극한 테스트 (5개 실험)
# =============================================================================

log "=== 시나리오 3: Min Write Buffer Number To Merge 극한 테스트 ==="

# 실험 3-1: Merge 임계값 1 (즉시 병합 - 높은 I/O)
run_experiment "scenario3_merge1_immediate" \
    67108864 \
    8 \
    1

# 실험 3-2: Merge 임계값 2 (빠른 병합)
run_experiment "scenario3_merge2_fast" \
    67108864 \
    8 \
    2

# 실험 3-3: Merge 임계값 4 (중간 병합)
run_experiment "scenario3_merge4_medium" \
    67108864 \
    8 \
    4

# 실험 3-4: Merge 임계값 6 (늦은 병합)
run_experiment "scenario3_merge6_slow" \
    67108864 \
    8 \
    6

# 실험 3-5: Merge 임계값 8 (최대 지연 병합 - 메모리 압박)
run_experiment "scenario3_merge8_delayed" \
    67108864 \
    8 \
    8



# =============================================================================
# 실험 완료 및 결과 요약
# =============================================================================

log "모든 실험 완료!"
log "결과 파일 위치: $RESULTS_DIR"

# 결과 요약 파일 생성
summary_file="$RESULTS_DIR/experiment_summary.txt"
echo "RocksDB Write Buffer 최적화 실험 요약 (개선된 버전)" > "$summary_file"
echo "실험 일시: $(date)" >> "$summary_file"
echo "실험 환경: CPU 4코어, 메모리 8.59GB" >> "$summary_file"
echo "키-값 쌍 수: $NUM_KEYS" >> "$summary_file"
echo "값 크기: ${VALUE_SIZE}B" >> "$summary_file"
echo "스레드 수: $NUM_THREADS" >> "$summary_file"
echo "예상 총 데이터 크기: $(($NUM_KEYS * $VALUE_SIZE / 1024 / 1024 / 1024))GB" >> "$summary_file"
echo "" >> "$summary_file"

echo "실험 시나리오별 요약:" >> "$summary_file"
echo "1. Write Buffer Size 극한 테스트: 8MB ~ 512MB (5개 실험)" >> "$summary_file"
echo "2. Max Write Buffer Number 극한 테스트: 1개 ~ 16개 (5개 실험)" >> "$summary_file"
echo "3. Min Write Buffer Number To Merge 극한 테스트: 1 ~ 8 (5개 실험)" >> "$summary_file"
echo "" >> "$summary_file"

echo "실험 파일 목록:" >> "$summary_file"
ls -la "$RESULTS_DIR"/*.txt >> "$summary_file"

log "실험 요약 파일 생성: $summary_file"
log "총 15개 실험 완료 - 극명한 성능 차이 분석 가능"
log "실험 자동화 스크립트 실행 완료" 