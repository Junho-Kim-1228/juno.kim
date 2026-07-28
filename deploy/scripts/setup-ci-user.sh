#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEPLOY_USER="juno-deploy"
readonly DEPLOY_COMMAND="/usr/local/sbin/juno-kim-deploy"
readonly SUDOERS_FILE="/etc/sudoers.d/juno-kim-deploy"

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this script as root." >&2
    exit 1
fi

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 PUBLIC_KEY_FILE CI_DEPLOY_SCRIPT" >&2
    exit 1
fi

public_key_file="$1"
deploy_script="$2"

if [[ ! -f "${public_key_file}" || ! -f "${deploy_script}" ]]; then
    echo "The public key and CI deployment script must both exist." >&2
    exit 1
fi

public_key="$(tr -d '\r\n' < "${public_key_file}")"
if [[ ! "${public_key}" =~ ^ssh-ed25519\ [A-Za-z0-9+/=]+\ github-actions-juno-kim$ ]]; then
    echo "Unexpected deployment public key format." >&2
    exit 1
fi

if ! id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
    adduser \
        --disabled-password \
        --gecos "" \
        --home "/home/${DEPLOY_USER}" \
        --shell /bin/bash \
        "${DEPLOY_USER}"
fi

install -o root -g root -m 0755 "${deploy_script}" "${DEPLOY_COMMAND}"
install -d -o "${DEPLOY_USER}" -g "${DEPLOY_USER}" -m 0700 "/home/${DEPLOY_USER}/.ssh"

forced_options='command="sudo -n /usr/local/sbin/juno-kim-deploy",no-agent-forwarding,no-port-forwarding,no-pty,no-user-rc,no-X11-forwarding'
printf '%s %s\n' "${forced_options}" "${public_key}" > "/home/${DEPLOY_USER}/.ssh/authorized_keys"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh/authorized_keys"
chmod 0600 "/home/${DEPLOY_USER}/.ssh/authorized_keys"

printf '%s\n' \
    "${DEPLOY_USER} ALL=(root) NOPASSWD: ${DEPLOY_COMMAND}" \
    > "${SUDOERS_FILE}"
chmod 0440 "${SUDOERS_FILE}"
visudo -cf "${SUDOERS_FILE}"

echo "Restricted CI deployment user installed: ${DEPLOY_USER}"
