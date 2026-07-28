#!/usr/bin/env bash
set -euo pipefail

readonly APP_NAME="juno-kim"
readonly APP_USER="juno-kim"
readonly APP_ROOT="/var/www/${APP_NAME}"
readonly ENV_FILE="/etc/${APP_NAME}/${APP_NAME}.env"
readonly PROTECTED_SERVICE="game-recruit-bot.service"
readonly APP_SERVICE="${APP_NAME}.service"

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
fi

for command_name in git python3 npm systemctl nginx curl; do
    command -v "${command_name}" >/dev/null 2>&1 || {
        echo "Missing required command: ${command_name}" >&2
        exit 1
    }
done

systemctl is-active --quiet "${PROTECTED_SERVICE}" || {
    echo "Protected service ${PROTECTED_SERVICE} is not active; deployment aborted." >&2
    exit 1
}

current_branch="$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" branch --show-current)"
if [[ "${current_branch}" != "main" ]]; then
    echo "Expected main branch, found '${current_branch:-detached HEAD}'." >&2
    echo "Run 'sudo -u ${APP_USER} git -C ${APP_ROOT} switch main' before deploying." >&2
    exit 1
fi

if [[ -n "$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" status --porcelain)" ]]; then
    echo "Deployment worktree is not clean; deployment aborted." >&2
    exit 1
fi

previous_revision="$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" rev-parse HEAD)"
backup_id="$(date -u +%Y%m%dT%H%M%SZ)-${previous_revision:0:12}"
"${APP_ROOT}/deploy/scripts/backup.sh" "${backup_id}"

echo "Updating main from origin (previous revision: ${previous_revision})"
sudo -u "${APP_USER}" git -C "${APP_ROOT}" fetch origin main
sudo -u "${APP_USER}" git -C "${APP_ROOT}" merge --ff-only origin/main

if [[ ! -x "${APP_ROOT}/.venv/bin/python" ]]; then
    sudo -u "${APP_USER}" python3 -m venv "${APP_ROOT}/.venv"
fi

sudo -u "${APP_USER}" "${APP_ROOT}/.venv/bin/python" -m pip install --upgrade pip
sudo -u "${APP_USER}" "${APP_ROOT}/.venv/bin/pip" install \
    --requirement "${APP_ROOT}/backend/requirements/production.txt"

sudo -u "${APP_USER}" env DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_ENV_FILE="${ENV_FILE}" \
    "${APP_ROOT}/.venv/bin/python" "${APP_ROOT}/backend/manage.py" migrate --noinput
sudo -u "${APP_USER}" env DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_ENV_FILE="${ENV_FILE}" \
    "${APP_ROOT}/.venv/bin/python" "${APP_ROOT}/backend/manage.py" collectstatic --noinput
sudo -u "${APP_USER}" env DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_ENV_FILE="${ENV_FILE}" \
    "${APP_ROOT}/.venv/bin/python" "${APP_ROOT}/backend/manage.py" check --deploy

sudo -u "${APP_USER}" env HOME="${APP_ROOT}" npm --prefix "${APP_ROOT}/frontend" ci
sudo -u "${APP_USER}" env HOME="${APP_ROOT}" npm --prefix "${APP_ROOT}/frontend" run build

systemctl restart "${APP_SERVICE}"
nginx -t
systemctl reload nginx

health_url='http://localhost/api/v1/health/'
for attempt in $(seq 1 20); do
    if curl --fail --silent --output /dev/null \
        --unix-socket "/run/${APP_NAME}/gunicorn.sock" \
        --header "Host: juno.kim" \
        --header "X-Forwarded-Proto: https" \
        "${health_url}"; then
        break
    fi
    if [[ ${attempt} -eq 20 ]]; then
        echo "Application health check failed after ${attempt} attempts." >&2
        exit 1
    fi
    sleep 1
done

systemctl is-active --quiet "${APP_SERVICE}"
systemctl is-active --quiet "${PROTECTED_SERVICE}"

echo "Deployment complete: $(sudo -u "${APP_USER}" git -C "${APP_ROOT}" rev-parse --short HEAD)"
echo "Protected service remains active: ${PROTECTED_SERVICE}"
echo "Application logs: sudo journalctl -u ${APP_SERVICE} -n 100 --no-pager"
