#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

readonly APP_NAME="juno-kim"
readonly APP_USER="juno-kim"
readonly APP_ROOT="/var/www/${APP_NAME}"
readonly ENV_FILE="/etc/${APP_NAME}/${APP_NAME}.env"
readonly MYSQL_CLIENT_CONFIG="/etc/${APP_NAME}/mysql-client.cnf"
readonly DATABASE_NAME="juno_kim"
readonly BACKUP_ROOT="/var/backups/${APP_NAME}"
readonly AWS_REGION="ap-northeast-2"
readonly LOCK_FILE="/run/lock/${APP_NAME}-s3-backup.lock"

if [[ ${EUID} -ne 0 ]]; then
    echo "This backup entrypoint must run as root." >&2
    exit 1
fi

for command_name in aws awk date flock git gzip install mktemp mysqldump rm rmdir sha256sum tar; do
    command -v "${command_name}" >/dev/null 2>&1 || {
        echo "Missing required command: ${command_name}" >&2
        exit 1
    }
done

if [[ ! -r "${ENV_FILE}" || ! -r "${MYSQL_CLIENT_CONFIG}" ]]; then
    echo "Required protected configuration is unavailable." >&2
    exit 1
fi

backup_bucket="$(
    awk -F= '
        $1 == "S3_BACKUP_BUCKET" {
            value = substr($0, index($0, "=") + 1)
        }
        END { print value }
    ' "${ENV_FILE}"
)"

if [[ ! "${backup_bucket}" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]]; then
    echo "S3_BACKUP_BUCKET is missing or invalid." >&2
    exit 1
fi

install -d -m 0750 -o root -g "${APP_USER}" "${BACKUP_ROOT}"

exec 9>"${LOCK_FILE}"
flock --nonblock 9 || {
    echo "Another ${APP_NAME} S3 backup is already running." >&2
    exit 1
}

backup_id="$(date -u +%Y%m%dT%H%M%SZ)"
object_prefix="backups/${backup_id}"
temp_dir="$(mktemp -d "${BACKUP_ROOT}/s3-upload.${backup_id}.XXXXXX")"

cleanup() {
    rm -f -- \
        "${temp_dir}/database.sql.gz" \
        "${temp_dir}/media.tar.gz" \
        "${temp_dir}/git-revision.txt" \
        "${temp_dir}/SHA256SUMS" || true
    rmdir -- "${temp_dir}" 2>/dev/null || true
}
trap cleanup EXIT

git -c safe.directory="${APP_ROOT}" -C "${APP_ROOT}" rev-parse HEAD \
    > "${temp_dir}/git-revision.txt"

mysqldump \
    --defaults-extra-file="${MYSQL_CLIENT_CONFIG}" \
    --single-transaction \
    --no-tablespaces \
    --routines \
    --triggers \
    "${DATABASE_NAME}" | gzip -9 > "${temp_dir}/database.sql.gz"

if [[ -d "${APP_ROOT}/backend/media" ]]; then
    tar -C "${APP_ROOT}/backend" -czf "${temp_dir}/media.tar.gz" media
else
    tar -C "${temp_dir}" -czf "${temp_dir}/media.tar.gz" --files-from /dev/null
fi

(
    cd "${temp_dir}"
    sha256sum database.sql.gz media.tar.gz git-revision.txt > SHA256SUMS
)

for backup_file in database.sql.gz media.tar.gz git-revision.txt SHA256SUMS; do
    aws s3api put-object \
        --region "${AWS_REGION}" \
        --bucket "${backup_bucket}" \
        --key "${object_prefix}/${backup_file}" \
        --body "${temp_dir}/${backup_file}" \
        --server-side-encryption AES256 \
        --no-cli-pager \
        >/dev/null
done

echo "S3 backup completed: s3://${backup_bucket}/${object_prefix}/"
