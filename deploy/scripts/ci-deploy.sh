#!/usr/bin/env bash
set -Eeuo pipefail

umask 027

readonly APP_NAME="juno-kim"
readonly APP_USER="juno-kim"
readonly APP_ROOT="/var/www/${APP_NAME}"
readonly ENV_FILE="/etc/${APP_NAME}/${APP_NAME}.env"
readonly MYSQL_CLIENT_CONFIG="/etc/${APP_NAME}/mysql-client.cnf"
readonly DATABASE_NAME="juno_kim"
readonly BACKUP_ROOT="/var/backups/${APP_NAME}"
readonly PROTECTED_SERVICE="game-recruit-bot.service"
readonly APP_SERVICE="${APP_NAME}.service"
readonly LOCK_FILE="/run/lock/${APP_NAME}-deploy.lock"
readonly NGINX_SITE="/etc/nginx/sites-available/${APP_NAME}.conf"
readonly NGINX_SITE_BACKUP="${NGINX_SITE}.deploy-backup"
readonly SYSTEMD_DIR="/etc/systemd/system"

if [[ ${EUID} -ne 0 ]]; then
    echo "This deployment entrypoint must run as root." >&2
    exit 1
fi

for command_name in aws flock git python3 npm systemctl nginx curl mysqldump gzip tar; do
    command -v "${command_name}" >/dev/null 2>&1 || {
        echo "Missing required command: ${command_name}" >&2
        exit 1
    }
done

exec 9>"${LOCK_FILE}"
flock --nonblock 9 || {
    echo "Another ${APP_NAME} deployment is already running." >&2
    exit 1
}

systemctl is-active --quiet "${PROTECTED_SERVICE}" || {
    echo "Protected service ${PROTECTED_SERVICE} is not active; deployment aborted." >&2
    exit 1
}

current_branch="$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" branch --show-current)"
if [[ "${current_branch}" != "main" ]]; then
    echo "Expected main branch, found '${current_branch:-detached HEAD}'." >&2
    exit 1
fi

if [[ -n "$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" status --porcelain)" ]]; then
    echo "Deployment worktree is not clean; deployment aborted." >&2
    exit 1
fi

if [[ ! -f "${MYSQL_CLIENT_CONFIG}" ]]; then
    echo "Missing ${MYSQL_CLIENT_CONFIG}; deployment aborted." >&2
    exit 1
fi

admin_url="$(awk -F= '$1 == "ADMIN_URL" {print substr($0, index($0, "=") + 1); exit}' "${ENV_FILE}")"
admin_path="${admin_url#/}"
admin_path="${admin_path%/}"
if [[ "${admin_path}" == "admin" || ! "${admin_path}" =~ ^[a-z0-9][a-z0-9-]{19,79}$ ]]; then
    echo "ADMIN_URL must be a non-default, 20+ character lowercase path." >&2
    exit 1
fi

nginx_rendered_config="$(mktemp)"
trap 'rm -f "${nginx_rendered_config}"' EXIT
sed "s|__ADMIN_PATH__|${admin_path}|g" \
    "${APP_ROOT}/deploy/nginx/juno-kim.conf" > "${nginx_rendered_config}"

previous_revision="$(sudo -u "${APP_USER}" git -C "${APP_ROOT}" rev-parse HEAD)"
backup_id="$(date -u +%Y%m%dT%H%M%SZ)-${previous_revision:0:12}"
backup_dir="${BACKUP_ROOT}/${backup_id}"

install -d -m 0750 -o root -g "${APP_USER}" "${backup_dir}"
printf '%s\n' "${previous_revision}" > "${backup_dir}/git-revision.txt"
mysqldump \
    --defaults-extra-file="${MYSQL_CLIENT_CONFIG}" \
    --single-transaction \
    --no-tablespaces \
    --routines \
    --triggers \
    "${DATABASE_NAME}" | gzip -9 > "${backup_dir}/database.sql.gz"

if [[ -d "${APP_ROOT}/backend/media" ]]; then
    tar -C "${APP_ROOT}/backend" -czf "${backup_dir}/media.tar.gz" media
fi

chmod 0640 "${backup_dir}"/*
echo "Backup created: ${backup_dir}"

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
sudo -u "${APP_USER}" env HOME="${APP_ROOT}" VITE_ADMIN_URL="/${admin_path}/" \
    npm --prefix "${APP_ROOT}/frontend" run build

cp --preserve=mode,ownership,timestamps "${NGINX_SITE}" "${NGINX_SITE_BACKUP}"
install -o root -g root -m 0644 \
    "${nginx_rendered_config}" \
    "${NGINX_SITE}"
if ! nginx -t; then
    echo "Nginx configuration validation failed; restoring previous site configuration." >&2
    cp --preserve=mode,ownership,timestamps "${NGINX_SITE_BACKUP}" "${NGINX_SITE}"
    rm -f "${NGINX_SITE_BACKUP}"
    nginx -t
    exit 1
fi
rm -f "${NGINX_SITE_BACKUP}"

install -o root -g root -m 0644 \
    "${APP_ROOT}/deploy/systemd/juno-kim.service" \
    "${SYSTEMD_DIR}/juno-kim.service"
install -o root -g root -m 0644 \
    "${APP_ROOT}/deploy/systemd/juno-kim-monitor.service" \
    "${SYSTEMD_DIR}/juno-kim-monitor.service"
install -o root -g root -m 0644 \
    "${APP_ROOT}/deploy/systemd/juno-kim-monitor.timer" \
    "${SYSTEMD_DIR}/juno-kim-monitor.timer"
install -o root -g root -m 0755 \
    "${APP_ROOT}/deploy/scripts/backup-to-s3.sh" \
    "/usr/local/sbin/juno-kim-backup-to-s3"
install -o root -g root -m 0644 \
    "${APP_ROOT}/deploy/systemd/juno-kim-backup.service" \
    "${SYSTEMD_DIR}/juno-kim-backup.service"
install -o root -g root -m 0644 \
    "${APP_ROOT}/deploy/systemd/juno-kim-backup.timer" \
    "${SYSTEMD_DIR}/juno-kim-backup.timer"
systemctl daemon-reload
systemctl enable --now juno-kim-monitor.timer
systemctl enable --now juno-kim-backup.timer

systemctl restart "${APP_SERVICE}"
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
systemctl is-active --quiet juno-kim-monitor.timer
systemctl is-active --quiet juno-kim-backup.timer
systemctl is-active --quiet "${PROTECTED_SERVICE}"

echo "Deployment complete: $(sudo -u "${APP_USER}" git -C "${APP_ROOT}" rev-parse --short HEAD)"
echo "Protected service remains active: ${PROTECTED_SERVICE}"
