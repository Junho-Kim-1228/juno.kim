#!/usr/bin/env bash
set -euo pipefail

readonly APP_NAME="juno-kim"
readonly APP_USER="juno-kim"
readonly APP_ROOT="/var/www/${APP_NAME}"
readonly ENV_FILE="/etc/${APP_NAME}/${APP_NAME}.env"
readonly APP_SERVICE="${APP_NAME}.service"
readonly PROTECTED_SERVICE="game-recruit-bot.service"

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this script as root: sudo $0 <git-revision>" >&2
    exit 1
fi

target_revision="${1:-}"
if [[ -z "${target_revision}" ]]; then
    echo "Usage: sudo $0 <git-revision>" >&2
    exit 1
fi

systemctl is-active --quiet "${PROTECTED_SERVICE}" || {
    echo "Protected service ${PROTECTED_SERVICE} is not active; rollback aborted." >&2
    exit 1
}

if [[ -n "$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" status --porcelain)" ]]; then
    echo "Deployment worktree is not clean; rollback aborted." >&2
    exit 1
fi

sudo -u "${APP_USER}" git -C "${APP_ROOT}" cat-file -e "${target_revision}^{commit}"
"${APP_ROOT}/deploy/scripts/backup.sh" "pre-rollback-$(date -u +%Y%m%dT%H%M%SZ)"
sudo -u "${APP_USER}" git -C "${APP_ROOT}" switch --detach "${target_revision}"

sudo -u "${APP_USER}" "${APP_ROOT}/.venv/bin/pip" install \
    --requirement "${APP_ROOT}/backend/requirements/production.txt"
sudo -u "${APP_USER}" env DJANGO_SETTINGS_MODULE=config.settings.production DJANGO_ENV_FILE="${ENV_FILE}" \
    "${APP_ROOT}/.venv/bin/python" "${APP_ROOT}/backend/manage.py" collectstatic --noinput
sudo -u "${APP_USER}" env HOME="${APP_ROOT}" npm --prefix "${APP_ROOT}/frontend" ci
sudo -u "${APP_USER}" env HOME="${APP_ROOT}" npm --prefix "${APP_ROOT}/frontend" run build

systemctl restart "${APP_SERVICE}"
nginx -t
systemctl reload nginx
systemctl is-active --quiet "${APP_SERVICE}"
systemctl is-active --quiet "${PROTECTED_SERVICE}"

echo "Code rollback complete at ${target_revision}."
echo "Database migrations are not reversed automatically. Restore a reviewed backup manually if required."
echo "Return to normal deployments with: sudo -u ${APP_USER} git -C ${APP_ROOT} switch main"
