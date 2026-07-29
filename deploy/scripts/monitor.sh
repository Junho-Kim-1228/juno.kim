#!/usr/bin/env bash
set -Eeuo pipefail

readonly APP_SERVICE="juno-kim.service"
readonly APP_SOCKET="/run/juno-kim/gunicorn.sock"
readonly HEALTH_URL="http://localhost/api/v1/health/"
readonly DISK_WARNING_PERCENT="${DISK_WARNING_PERCENT:-85}"
readonly MEMORY_WARNING_PERCENT="${MEMORY_WARNING_PERCENT:-90}"

failures=0

report_failure() {
    printf 'monitor_check_failed component=%s detail=%s\n' "$1" "$2" >&2
    failures=$((failures + 1))
}

if ! systemctl is-active --quiet "${APP_SERVICE}"; then
    report_failure "service" "inactive"
fi

if ! curl \
    --fail \
    --silent \
    --show-error \
    --max-time 10 \
    --output /dev/null \
    --unix-socket "${APP_SOCKET}" \
    --header "Host: juno.kim" \
    --header "X-Forwarded-Proto: https" \
    "${HEALTH_URL}"; then
    report_failure "health_endpoint" "request_failed"
fi

disk_used_percent="$(df -P /var | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')"
if [[ ! "${disk_used_percent}" =~ ^[0-9]+$ ]]; then
    report_failure "disk" "measurement_failed"
elif ((disk_used_percent >= DISK_WARNING_PERCENT)); then
    report_failure "disk" "usage_${disk_used_percent}_percent"
fi

read -r memory_total_kb memory_available_kb < <(
    awk '
        /^MemTotal:/ {total=$2}
        /^MemAvailable:/ {available=$2}
        END {print total, available}
    ' /proc/meminfo
)
if [[ ! "${memory_total_kb}" =~ ^[0-9]+$ ]] || [[ ! "${memory_available_kb}" =~ ^[0-9]+$ ]] || ((memory_total_kb == 0)); then
    report_failure "memory" "measurement_failed"
else
    memory_used_percent=$(((memory_total_kb - memory_available_kb) * 100 / memory_total_kb))
    if ((memory_used_percent >= MEMORY_WARNING_PERCENT)); then
        report_failure "memory" "usage_${memory_used_percent}_percent"
    fi
fi

if ((failures > 0)); then
    exit 1
fi

printf 'monitor_check_ok disk_usage=%s_percent memory_usage=%s_percent\n' \
    "${disk_used_percent}" "${memory_used_percent}"
