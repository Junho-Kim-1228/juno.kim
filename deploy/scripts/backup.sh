#!/usr/bin/env bash
set -euo pipefail

readonly APP_NAME="juno-kim"
readonly APP_ROOT="/var/www/${APP_NAME}"
readonly BACKUP_ROOT="/var/backups/${APP_NAME}"
readonly MYSQL_CLIENT_CONFIG="/etc/${APP_NAME}/mysql-client.cnf"
readonly DATABASE_NAME="juno_kim"

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
fi

if [[ ! -f "${MYSQL_CLIENT_CONFIG}" ]]; then
    echo "Missing ${MYSQL_CLIENT_CONFIG}" >&2
    exit 1
fi

backup_id="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
backup_dir="${BACKUP_ROOT}/${backup_id}"

install -d -m 0750 -o root -g "${APP_NAME}" "${backup_dir}"

git -C "${APP_ROOT}" rev-parse HEAD > "${backup_dir}/git-revision.txt"
mysqldump \
    --defaults-extra-file="${MYSQL_CLIENT_CONFIG}" \
    --single-transaction \
    --routines \
    --triggers \
    "${DATABASE_NAME}" | gzip -9 > "${backup_dir}/database.sql.gz"

if [[ -d "${APP_ROOT}/backend/media" ]]; then
    tar -C "${APP_ROOT}/backend" -czf "${backup_dir}/media.tar.gz" media
fi

chmod 0640 "${backup_dir}"/*
echo "Backup created: ${backup_dir}"
echo "Backups are not deleted automatically. Apply an explicit retention policy after off-instance copies exist."
