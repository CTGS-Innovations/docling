#!/bin/bash

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_FILES=${1:-5}

get_question_data() {
    local file="$1"
    local question_num="$2"
    
    local line=$(grep "Q${question_num}\." "$file" 2>/dev/null || true)
    if [[ -n "$line" ]]; then
        local bracket_content=$(echo "$line" | grep -oE '\[S1: [0-9]+ A[0-9]+: .*\]' || true)
        if [[ -n "$bracket_content" ]]; then
            local seed=$(echo "$bracket_content" | sed -E 's/\[S1: ([0-9]+) A[0-9]+: .*\]/\1/')
            local answer=$(echo "$bracket_content" | sed -E 's/\[S1: [0-9]+ A[0-9]+: (.*)\]/\1/')
            echo "[${seed}] ${answer}"
        fi
    fi
}

main() {
    cd "$SCRIPT_DIR"
    local -a rubric_files
    readarray -t rubric_files < <(find . -name "rubric_*.md" -type f | sort -r | head -$MAX_FILES)
    
    for q in {1..50}; do
        for file in "${rubric_files[@]}"; do
            local filename=$(basename "$file" | sed 's/rubric_//' | sed 's/.md//')
            local result=$(get_question_data "$file" "$q")
            if [[ -n "$result" ]]; then
                echo "${filename}: Q${q}:${result}"
            fi
        done
    done
}

main "$@"