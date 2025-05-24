#!/bin/bash

# RocksDB Write Buffer 최적화 실험 스크립트
# 작성자: 컴퓨터공학과 4학년
# 목적: write_buffer_size 등 설정이 성능에 미치는 영향 분석

set -e  # 에러 발생시 즉시 종료

# =============================================================================
# 실험 환경 설정
# =============================================================================

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 실험 디렉토리 설정
EXPERIMENT_DIR="$(pwd)/write_buffer_experiment"
DB_PATH="${EXPERIMENT_DIR}/rocksdb_test"
RESULTS_DIR="${EXPERIMENT_DIR}/results"
LOGS_DIR="${EXPERIMENT_DIR}/logs"

# db_bench 경로 (수정 필요시)
DB_BENCH_PATH="./db_bench"

# 실험 설정
NUM_KEYS=1000000           # 실험용 키 개수
NUM_ITERATIONS=3           # 반복 실험 횟수
VALUE_SIZE=1024           # 값 크기 (bytes)

# =============================================================================
# 함수 정의
# =============================================================================

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} RocksDB Write Buffer 최적화 실험${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 검증 함수
check_environment() {
    print_step "실험 환경 검증 중..."
    
    # db_bench 존재 확인
    if [ ! -f "$DB_BENCH_PATH" ]; then
        print_error "db_bench를 찾을 수 없습니다: $DB_BENCH_PATH"
        print_info "RocksDB를 빌드하고 db_bench 경로를 확인해주세요"
        exit 1
    fi
    
    # 디렉토리 생성
    mkdir -p "$EXPERIMENT_DIR" "$RESULTS_DIR" "$LOGS_DIR"
    
    # 시스템 정보 수집
    echo "=== 시스템 정보 ===" > "$LOGS_DIR/system_info.txt"
    uname -a >> "$LOGS_DIR/system_info.txt"
    echo "" >> "$LOGS_DIR/system_info.txt"
    echo "=== CPU 정보 ===" >> "$LOGS_DIR/system_info.txt"
    lscpu >> "$LOGS_DIR/system_info.txt"
    echo "" >> "$LOGS_DIR/system_info.txt"
    echo "=== 메모리 정보 ===" >> "$LOGS_DIR/system_info.txt"
    free -h >> "$LOGS_DIR/system_info.txt"
    echo "" >> "$LOGS_DIR/system_info.txt"
    echo "=== 디스크 정보 ===" >> "$LOGS_DIR/system_info.txt"
    df -h >> "$LOGS_DIR/system_info.txt"
    
    print_info "환경 검증 완료"
}

# 데이터베이스 초기화 함수
cleanup_db() {
    if [ -d "$DB_PATH" ]; then
        rm -rf "$DB_PATH"
    fi
    mkdir -p "$DB_PATH"
}

# 시스템 모니터링 시작
start_monitoring() {
    local test_name=$1
    local monitor_log="$LOGS_DIR/${test_name}_monitor.log"
    
    # CPU, 메모리, I/O 모니터링 (백그라운드)
    {
        echo "timestamp,cpu_usage,memory_usage_mb,io_read_kb,io_write_kb" > "$monitor_log"
        while true; do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
            memory_usage=$(free -m | awk 'NR==2{printf "%d", $3}')
            io_stats=$(iostat -d 1 1 | tail -n +4 | head -1 | awk '{print $3","$4}')
            echo "$timestamp,$cpu_usage,$memory_usage,$io_stats" >> "$monitor_log"
            sleep 5
        done
    } &
    
    echo $! > "$LOGS_DIR/${test_name}_monitor.pid"
}

# 시스템 모니터링 종료
stop_monitoring() {
    local test_name=$1
    local pid_file="$LOGS_DIR/${test_name}_monitor.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        kill $pid 2>/dev/null || true
        rm "$pid_file"
    fi
}

# 개별 벤치마크 실행 함수
run_benchmark() {
    local benchmark_type=$1
    local write_buffer_size=$2
    local max_write_buffer_number=$3
    local min_write_buffer_number_to_merge=$4
    local iteration=$5
    
    local test_name="${benchmark_type}_${write_buffer_size}_${max_write_buffer_number}_${min_write_buffer_number_to_merge}_iter${iteration}"
    local result_file="$RESULTS_DIR/${test_name}.txt"
    
    print_info "실행 중: $test_name"
    
    # 데이터베이스 초기화
    cleanup_db
    
    # 모니터링 시작
    start_monitoring "$test_name"
    
    # 벤치마크 실행
    local start_time=$(date +%s)
    
    "$DB_BENCH_PATH" \
        --benchmarks="$benchmark_type" \
        --db="$DB_PATH" \
        --num="$NUM_KEYS" \
        --value_size="$VALUE_SIZE" \
        --write_buffer_size="$write_buffer_size" \
        --max_write_buffer_number="$max_write_buffer_number" \
        --min_write_buffer_number_to_merge="$min_write_buffer_number_to_merge" \
        --statistics=true \
        --histogram=true \
        --stats_per_interval=1 \
        --stats_interval_seconds=10 \
        > "$result_file" 2>&1
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # 모니터링 종료
    stop_monitoring "$test_name"
    
    print_info "완료: $test_name (소요시간: ${duration}초)"
}

# 실험 설정 정의
declare -a WRITE_BUFFER_SIZES=("16777216" "67108864" "134217728" "268435456" "536870912")  # 16MB, 64MB, 128MB, 256MB, 512MB
declare -a WRITE_BUFFER_SIZE_LABELS=("16MB" "64MB" "128MB" "256MB" "512MB")
declare -a MAX_WRITE_BUFFER_NUMBERS=("2" "4" "6")
declare -a MIN_WRITE_BUFFER_NUMBER_TO_MERGE=("1" "2" "3")
declare -a BENCHMARKS=("fillrandom" "readrandom" "overwrite")

# =============================================================================
# 메인 실험 실행
# =============================================================================

main() {
    print_header
    
    # 환경 검증
    check_environment
    
    # 실험 시작 시간 기록
    local experiment_start=$(date '+%Y-%m-%d %H:%M:%S')
    echo "실험 시작 시간: $experiment_start" > "$LOGS_DIR/experiment_log.txt"
    
    print_step "Write Buffer Size 영향 분석 실험 시작"
    
    # 기본 실험: write_buffer_size만 변경
    local total_tests=$((${#WRITE_BUFFER_SIZES[@]} * ${#BENCHMARKS[@]} * NUM_ITERATIONS))
    local current_test=0
    
    for benchmark in "${BENCHMARKS[@]}"; do
        for i in "${!WRITE_BUFFER_SIZES[@]}"; do
            local size="${WRITE_BUFFER_SIZES[$i]}"
            local label="${WRITE_BUFFER_SIZE_LABELS[$i]}"
            
            print_step "실험 진행: $benchmark with write_buffer_size=$label"
            
            for iteration in $(seq 1 $NUM_ITERATIONS); do
                current_test=$((current_test + 1))
                print_info "진행률: $current_test/$total_tests"
                
                # 기본 설정으로 실행 (max_write_buffer_number=2, min_write_buffer_number_to_merge=1)
                run_benchmark "$benchmark" "$size" "2" "1" "$iteration"
            done
        done
    done
    
    print_step "추가 실험: 최적 write_buffer_size에서 다른 파라미터 조합 테스트"
    
    # 128MB(최적으로 예상되는 크기)에서 다른 파라미터 조합 테스트
    local optimal_size="134217728"  # 128MB
    
    for max_buffers in "${MAX_WRITE_BUFFER_NUMBERS[@]}"; do
        for min_merge in "${MIN_WRITE_BUFFER_NUMBER_TO_MERGE[@]}"; do
            # 기본 조합(2,1) 제외
            if [ "$max_buffers" != "2" ] || [ "$min_merge" != "1" ]; then
                for iteration in $(seq 1 $NUM_ITERATIONS); do
                    run_benchmark "fillrandom" "$optimal_size" "$max_buffers" "$min_merge" "$iteration"
                done
            fi
        done
    done
    
    # 실험 종료 시간 기록
    local experiment_end=$(date '+%Y-%m-%d %H:%M:%S')
    echo "실험 종료 시간: $experiment_end" >> "$LOGS_DIR/experiment_log.txt"
    
    print_step "모든 실험 완료!"
    print_info "결과 파일: $RESULTS_DIR"
    print_info "로그 파일: $LOGS_DIR"
    
    # Python 분석 스크립트 실행
    if command -v python3 &> /dev/null; then
        print_step "결과 분석 중..."
        python3 analyze_results.py
    else
        print_info "Python3가 설치되어 있지 않습니다. 수동으로 analyze_results.py를 실행해주세요."
    fi
}

# 스크립트 실행 (인터럽트 시 정리)
trap 'print_error "실험이 중단되었습니다."; exit 1' INT TERM

main "$@" 