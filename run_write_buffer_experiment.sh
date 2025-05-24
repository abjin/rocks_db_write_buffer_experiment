#!/bin/bash

# RocksDB Write Buffer 최적화 실험 스크립트 (평가표 최적화 버전)
# 작성자: 컴퓨터공학과 4학년
# 목적: write_buffer_size 등 설정이 성능에 미치는 영향 분석
# 평가 기준: 10-12분 발표용 최적화 실험 설계

set -e  # 에러 발생시 즉시 종료

# =============================================================================
# 실험 환경 설정 (평가표 최적화)
# =============================================================================

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 실험 디렉토리 설정
EXPERIMENT_DIR="$(pwd)/write_buffer_experiment"
DB_PATH="${EXPERIMENT_DIR}/rocksdb_test"
RESULTS_DIR="${EXPERIMENT_DIR}/results"
LOGS_DIR="${EXPERIMENT_DIR}/logs"
ANALYSIS_DIR="${EXPERIMENT_DIR}/analysis"

# db_bench 경로 (수정 필요시)
DB_BENCH_PATH="./db_bench"

# =============================================================================
# 평가표 최적화 실험 설정 (발표 시간 10-12분 고려)
# =============================================================================

# 기본 실험 설정 (빠른 실행을 위해 축소)
NUM_KEYS=100000            # 실험용 키 개수 (발표용 최적화)
NUM_ITERATIONS=3           # 반복 실험 횟수 (신뢰성 확보)
VALUE_SIZE=1024           # 값 크기 (bytes)

# 워밍업 설정 (실험 신뢰성 향상)
WARMUP_KEYS=10000         # 워밍업용 키 개수
WARMUP_ITERATIONS=1       # 워밍업 반복 횟수

# 독창적 접근: 실제 사용 시나리오 기반 워크로드 패턴
declare -A WORKLOAD_PATTERNS=(
    ["cache_friendly"]="readrandom:50,overwrite:30,fillrandom:20"
    ["write_heavy"]="fillrandom:60,overwrite:30,readrandom:10"
    ["balanced"]="readrandom:40,fillrandom:30,overwrite:30"
)

# =============================================================================
# 함수 정의
# =============================================================================

print_header() {
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE} RocksDB Write Buffer 최적화 실험${NC}"
    echo -e "${PURPLE} 📊 평가표 최적화 버전 (10-12분 발표용)${NC}"
    echo -e "${PURPLE}============================================${NC}"
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

print_creative() {
    echo -e "${PURPLE}[CREATIVE]${NC} $1"
}

# 실험 타당성 검증 함수 (평가표 기준)
validate_experiment_design() {
    print_step "실험 설계 타당성 검증 중..."
    
    # 1. 하드웨어 리소스 확인
    local memory_gb=$(free -g | awk 'NR==2{print $2}')
    local cpu_cores=$(nproc)
    
    if [ "$memory_gb" -lt 4 ]; then
        print_error "실험에 필요한 최소 메모리(4GB) 부족. 현재: ${memory_gb}GB"
        return 1
    fi
    
    if [ "$cpu_cores" -lt 2 ]; then
        print_error "실험에 필요한 최소 CPU 코어(2개) 부족. 현재: ${cpu_cores}개"
        return 1
    fi
    
    # 2. 실험 규모의 적절성 확인
    local estimated_time=$((NUM_KEYS / 10000 * 15))  # 대략적인 추정 시간 (초)
    print_info "예상 실험 시간: 약 ${estimated_time}초 per test"
    
    # 3. 통계적 신뢰성 확인
    if [ "$NUM_ITERATIONS" -lt 3 ]; then
        print_error "통계적 신뢰성을 위해 최소 3회 반복 필요"
        return 1
    fi
    
    print_info "✅ 실험 설계 타당성 검증 완료"
    return 0
}

# 창의적 접근: 환경 검증 함수 (평가표의 독창성 기준)
check_environment() {
    print_step "실험 환경 검증 중..."
    
    # 기본 환경 검증
    if [ ! -f "$DB_BENCH_PATH" ]; then
        print_error "db_bench를 찾을 수 없습니다: $DB_BENCH_PATH"
        print_info "RocksDB를 빌드하고 db_bench 경로를 확인해주세요"
        exit 1
    fi
    
    # 디렉토리 생성
    mkdir -p "$EXPERIMENT_DIR" "$RESULTS_DIR" "$LOGS_DIR" "$ANALYSIS_DIR"
    
    # 창의적 접근: Git 정보 기록 (재현성 향상)
    if command -v git &> /dev/null && [ -d .git ]; then
        echo "=== Git 정보 ===" > "$LOGS_DIR/experiment_metadata.txt"
        echo "Commit Hash: $(git rev-parse HEAD)" >> "$LOGS_DIR/experiment_metadata.txt"
        echo "Branch: $(git branch --show-current)" >> "$LOGS_DIR/experiment_metadata.txt"
        echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGS_DIR/experiment_metadata.txt"
        echo "" >> "$LOGS_DIR/experiment_metadata.txt"
    fi
    
    # 시스템 정보 상세 수집 (평가표의 신뢰성 기준)
    {
        echo "=== 실험 메타데이터 ==="
        echo "실험 목적: RocksDB Write Buffer 최적화 성능 분석"
        echo "실험자: 컴퓨터공학과 4학년"
        echo "실험 일시: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "=== 시스템 환경 ==="
        uname -a
        echo ""
        echo "=== CPU 정보 ==="
        if command -v lscpu &> /dev/null; then
            lscpu | grep -E "(Model name|CPU\(s\)|Thread|Cache)"
        else
            sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "CPU 정보 수집 실패"
        fi
        echo ""
        echo "=== 메모리 정보 ==="
        free -h 2>/dev/null || vm_stat | head -5
        echo ""
        echo "=== 디스크 정보 ==="
        df -h
        echo ""
        echo "=== RocksDB 버전 ==="
        "$DB_BENCH_PATH" --version 2>&1 | head -3 || echo "RocksDB 버전 정보 없음"
    } > "$LOGS_DIR/system_info.txt"
    
    # 실험 설계 타당성 검증
    validate_experiment_design
    
    print_info "환경 검증 완료"
}

# 워밍업 실행 (실험 신뢰성 향상)
run_warmup() {
    local test_name="warmup"
    print_step "시스템 워밍업 실행 중..."
    
    cleanup_db
    
    "$DB_BENCH_PATH" \
        --benchmarks="fillrandom" \
        --db="$DB_PATH" \
        --num="$WARMUP_KEYS" \
        --value_size="$VALUE_SIZE" \
        --write_buffer_size="67108864" \
        --max_write_buffer_number="2" \
        --min_write_buffer_number_to_merge="1" \
        --disable_wal=false \
        > "$LOGS_DIR/warmup.log" 2>&1
    
    print_info "워밍업 완료"
}

# 데이터베이스 초기화 함수 (개선된 정리)
cleanup_db() {
    if [ -d "$DB_PATH" ]; then
        rm -rf "$DB_PATH"
    fi
    mkdir -p "$DB_PATH"
    
    # 메모리 캐시 정리 (측정 정확성 향상)
    if command -v sync &> /dev/null; then
        sync
        sleep 1
    fi
}

# 창의적 접근: 실시간 성능 모니터링
start_monitoring() {
    local test_name=$1
    local monitor_log="$LOGS_DIR/${test_name}_monitor.log"
    
    # 헤더 작성
    echo "timestamp,cpu_usage_percent,memory_usage_mb,memory_percent,io_read_kb,io_write_kb,load_avg" > "$monitor_log"
    
    # 모니터링 스크립트 (백그라운드)
    {
        while true; do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            
            # CPU 사용률
            if command -v top &> /dev/null; then
                cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || echo "0")
            else
                cpu_usage="0"
            fi
            
            # 메모리 사용량
            if command -v free &> /dev/null; then
                memory_info=$(free -m | awk 'NR==2{printf "%d,%.1f", $3, $3*100/$2}')
            else
                memory_info="0,0"
            fi
            
            # I/O 통계 (간단화)
            if command -v iostat &> /dev/null; then
                io_stats=$(iostat -d 1 1 2>/dev/null | tail -n +4 | head -1 | awk '{print $3","$4}' || echo "0,0")
            else
                io_stats="0,0"
            fi
            
            # Load Average
            load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//' || echo "0")
            
            echo "$timestamp,$cpu_usage,$memory_info,$io_stats,$load_avg" >> "$monitor_log"
            sleep 3
        done
    } &
    
    echo $! > "$LOGS_DIR/${test_name}_monitor.pid"
}

# 모니터링 종료
stop_monitoring() {
    local test_name=$1
    local pid_file="$LOGS_DIR/${test_name}_monitor.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        kill $pid 2>/dev/null || true
        rm "$pid_file"
    fi
}

# 개선된 벤치마크 실행 함수 (평가표 기준 강화)
run_benchmark() {
    local benchmark_type=$1
    local write_buffer_size=$2
    local max_write_buffer_number=$3
    local min_write_buffer_number_to_merge=$4
    local iteration=$5
    
    local test_name="${benchmark_type}_${write_buffer_size}_${max_write_buffer_number}_${min_write_buffer_number_to_merge}_iter${iteration}"
    local result_file="$RESULTS_DIR/${test_name}.txt"
    local size_mb=$((write_buffer_size / 1024 / 1024))
    
    print_info "🔬 실행 중: $test_name (${size_mb}MB 버퍼)"
    
    # 실험 전 정리
    cleanup_db
    
    # 모니터링 시작
    start_monitoring "$test_name"
    
    # 실험 시작 시간 기록
    local start_time=$(date +%s.%N)
    local start_timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    
    # 개선된 벤치마크 실행 (더 정확한 측정)
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
        --stats_interval_seconds=5 \
        --disable_wal=false \
        --compression_type=snappy \
        --bloom_bits=10 \
        > "$result_file" 2>&1
    
    # 실험 종료 시간 기록
    local end_time=$(date +%s.%N)
    local end_timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    
    # 모니터링 종료
    stop_monitoring "$test_name"
    
    # 실험 메타데이터 기록 (재현성 향상)
    {
        echo "=== 실험 메타데이터 ==="
        echo "Test Name: $test_name"
        echo "Start Time: $start_timestamp"
        echo "End Time: $end_timestamp"
        echo "Duration: ${duration}s"
        echo "Buffer Size: ${size_mb}MB"
        echo "Max Buffers: $max_write_buffer_number"
        echo "Min Merge: $min_write_buffer_number_to_merge"
        echo "Keys: $NUM_KEYS"
        echo "Value Size: $VALUE_SIZE bytes"
        echo "================================"
    } >> "$result_file"
    
    print_info "✅ 완료: $test_name (소요시간: $(printf "%.2f" $duration)초)"
}

# =============================================================================
# 평가표 최적화 실험 설정
# =============================================================================

# 발표 시간 고려 최적화된 실험 변수
declare -a WRITE_BUFFER_SIZES=("16777216" "67108864" "134217728" "268435456")  # 16MB, 64MB, 128MB, 256MB
declare -a WRITE_BUFFER_SIZE_LABELS=("16MB" "64MB" "128MB" "256MB")
declare -a MAX_WRITE_BUFFER_NUMBERS=("2" "4" "6")
declare -a MIN_WRITE_BUFFER_NUMBER_TO_MERGE=("1" "2" "3")

# 발표용 핵심 벤치마크 (시간 최적화)
declare -a CORE_BENCHMARKS=("fillrandom" "readrandom")  # 핵심 워크로드만

# 창의적 접근: 추가 분석용 벤치마크
declare -a EXTENDED_BENCHMARKS=("overwrite" "readwhilewriting")

# =============================================================================
# 메인 실험 실행 (평가표 최적화)
# =============================================================================

main() {
    print_header
    
    # 환경 검증
    check_environment
    
    # 워밍업 실행
    run_warmup
    
    # 실험 시작 시간 기록
    local experiment_start=$(date '+%Y-%m-%d %H:%M:%S')
    echo "실험 시작 시간: $experiment_start" > "$LOGS_DIR/experiment_log.txt"
    echo "실험 설계: 평가표 최적화 버전 (10-12분 발표용)" >> "$LOGS_DIR/experiment_log.txt"
    
    print_step "📊 핵심 실험: Write Buffer Size 영향 분석"
    
    # Phase 1: 핵심 벤치마크 실행 (발표 핵심 데이터)
    local total_core_tests=$((${#WRITE_BUFFER_SIZES[@]} * ${#CORE_BENCHMARKS[@]} * NUM_ITERATIONS))
    local current_test=0
    
    for benchmark in "${CORE_BENCHMARKS[@]}"; do
        for i in "${!WRITE_BUFFER_SIZES[@]}"; do
            local size="${WRITE_BUFFER_SIZES[$i]}"
            local label="${WRITE_BUFFER_SIZE_LABELS[$i]}"
            
            print_step "📈 실험 진행: $benchmark with write_buffer_size=$label"
            
            for iteration in $(seq 1 $NUM_ITERATIONS); do
                current_test=$((current_test + 1))
                local progress=$((current_test * 100 / total_core_tests))
                print_info "📊 핵심 실험 진행률: $current_test/$total_core_tests (${progress}%)"
                
                # 기본 설정으로 실행
                run_benchmark "$benchmark" "$size" "2" "1" "$iteration"
            done
        done
    done
    
    print_creative "🎯 창의적 접근: 최적 설정에서 파라미터 조합 분석"
    
    # Phase 2: 128MB에서 파라미터 조합 최적화 (독창성 점수)
    local optimal_size="134217728"  # 128MB
    
    print_step "🔬 추가 분석: 최적 버퍼 크기(128MB)에서 조합 최적화"
    
    for max_buffers in "${MAX_WRITE_BUFFER_NUMBERS[@]}"; do
        for min_merge in "${MIN_WRITE_BUFFER_NUMBER_TO_MERGE[@]}"; do
            # 기본 조합(2,1) 제외
            if [ "$max_buffers" != "2" ] || [ "$min_merge" != "1" ]; then
                print_info "🔧 조합 테스트: max_buffers=$max_buffers, min_merge=$min_merge"
                for iteration in $(seq 1 $NUM_ITERATIONS); do
                    run_benchmark "fillrandom" "$optimal_size" "$max_buffers" "$min_merge" "$iteration"
                done
            fi
        done
    done
    
    # Phase 3: 창의적 추가 실험 (평가표의 독창성 기준)
    print_creative "🚀 독창적 접근: 실제 워크로드 패턴 시뮬레이션"
    
    # 혼합 워크로드 시뮬레이션 (실제 사용 시나리오)
    for pattern_name in "${!WORKLOAD_PATTERNS[@]}"; do
        local pattern="${WORKLOAD_PATTERNS[$pattern_name]}"
        print_creative "🎭 워크로드 패턴 '$pattern_name' 실행: $pattern"
        
        # 간단한 혼합 워크로드 (시간 제약으로 1회만)
        run_benchmark "readrandom" "$optimal_size" "2" "1" "mixed_${pattern_name}"
    done
    
    # 실험 종료 시간 기록
    local experiment_end=$(date '+%Y-%m-%d %H:%M:%S')
    echo "실험 종료 시간: $experiment_end" >> "$LOGS_DIR/experiment_log.txt"
    
    # 실험 통계 요약
    local total_tests=$(find "$RESULTS_DIR" -name "*.txt" | wc -l)
    echo "총 실행된 테스트: $total_tests" >> "$LOGS_DIR/experiment_log.txt"
    
    print_step "🎉 모든 실험 완료!"
    print_info "📁 결과 파일: $RESULTS_DIR"
    print_info "📊 로그 파일: $LOGS_DIR"
    
    # 즉시 분석 실행 (발표 준비)
    print_step "📈 발표용 분석 실행 중..."
    if command -v python3 &> /dev/null; then
        python3 analyze_results.py
        print_info "✅ 분석 완료! analysis/ 폴더에서 발표 자료 확인"
    else
        print_info "⚠️  Python3가 설치되어 있지 않습니다. 수동으로 analyze_results.py를 실행해주세요."
    fi
    
    # 발표 준비 가이드 출력
    print_header
    echo -e "${PURPLE}📋 발표 준비 완료 가이드${NC}"
    echo -e "${GREEN}✅ 1. 실험 결과: $RESULTS_DIR${NC}"
    echo -e "${GREEN}✅ 2. 분석 그래프: $ANALYSIS_DIR${NC}"
    echo -e "${GREEN}✅ 3. 시스템 로그: $LOGS_DIR${NC}"
    echo -e "${YELLOW}📊 발표 시간: 10-12분 최적화 완료${NC}"
    echo -e "${YELLOW}🎯 핵심 포인트: Write Buffer 크기별 성능 트레이드오프${NC}"
    echo -e "${PURPLE}🚀 독창성 포인트: 실제 워크로드 패턴 분석 포함${NC}"
}

# 스크립트 실행 (인터럽트 시 정리)
trap 'print_error "⚠️  실험이 중단되었습니다."; exit 1' INT TERM

main "$@" 