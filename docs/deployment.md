# AWS EC2 deployment

The production site is isolated from the existing Discord bot.

- SSH account: `ubuntu`
- Application account: `juno-kim`
- Source and virtual environment: `/var/www/juno-kim`
- Secrets: `/etc/juno-kim/juno-kim.env` (`0640`, `root:juno-kim`)
- Gunicorn: `/run/juno-kim/gunicorn.sock`
- systemd: `juno-kim.service`
- Nginx logs: `/var/log/nginx/juno-kim.access.log` and `juno-kim.error.log`
- Backups: `/var/backups/juno-kim`
- Protected service: `game-recruit-bot.service` (never restarted by website scripts)

Gunicorn uses a Unix socket instead of a TCP port. This avoids a new listener and
prevents a port collision with other processes on the shared instance. Nginx is
the only public entry point on ports 80 and 443.

## Initial server preparation

Install Nginx, MySQL 8, Certbot, Python build dependencies, and a supported
Node.js LTS release. Create the system account and clone the repository:

```bash
sudo adduser --system --group --home /var/www/juno-kim --shell /bin/bash juno-kim
sudo -u juno-kim git clone https://github.com/Junho-Kim-1228/juno.kim /var/www/juno-kim
sudo install -d -m 0750 -o root -g juno-kim /etc/juno-kim /var/backups/juno-kim
sudo install -d -m 0750 -o juno-kim -g www-data /var/www/juno-kim/backend/media
```

Create a dedicated `juno_kim` database and a `juno_kim@127.0.0.1` user that has
privileges only on that database. Copy the two examples in `deploy/env/` to
`/etc/juno-kim/`, replace all placeholders with independently generated values,
then apply these permissions:

```bash
sudo chown root:juno-kim /etc/juno-kim/juno-kim.env
sudo chmod 0640 /etc/juno-kim/juno-kim.env
sudo chown root:root /etc/juno-kim/mysql-client.cnf
sudo chmod 0600 /etc/juno-kim/mysql-client.cnf
```

Never reuse the Discord bot token or its environment file.

## Service and Nginx installation

```bash
sudo install -m 0644 /var/www/juno-kim/deploy/systemd/juno-kim.service /etc/systemd/system/juno-kim.service
sudo install -m 0644 /var/www/juno-kim/deploy/nginx/juno-kim.conf /etc/nginx/sites-available/juno-kim.conf
sudo ln -s /etc/nginx/sites-available/juno-kim.conf /etc/nginx/sites-enabled/juno-kim.conf
sudo systemctl daemon-reload
sudo systemctl enable juno-kim.service
sudo nginx -t
sudo systemctl reload nginx
```

Run the first deployment only after the environment and database are ready:

```bash
sudo /var/www/juno-kim/deploy/scripts/deploy.sh
sudo systemctl status juno-kim.service --no-pager
sudo journalctl -u juno-kim.service -n 100 --no-pager
```

## HTTPS

Confirm that the `juno.kim` A record resolves to the EC2 public IPv4 address and
that the security group allows inbound TCP 80 and 443. Then run:

```bash
sudo certbot --nginx -d juno.kim --redirect
sudo certbot renew --dry-run
```

After HTTPS works, keep `SECURE_HSTS_SECONDS=0` during initial observation. Raise
it gradually (for example to `3600`, then a longer period) only after HTTPS is
stable. Do not enable subdomain HSTS or preload until every subdomain is ready.

## Backup and rollback

Create a database/media backup before risky changes:

```bash
sudo /var/www/juno-kim/deploy/scripts/backup.sh
```

Roll back application code to a reviewed Git commit:

```bash
sudo /var/www/juno-kim/deploy/scripts/rollback.sh <git-revision>
```

The rollback script deliberately does not reverse database migrations. Review
the migration and the matching database backup before any data restore. Copy
backups off the EC2 instance; an on-instance backup alone does not protect
against volume loss.

## Verification

```bash
sudo systemctl is-active juno-kim.service
sudo systemctl is-active game-recruit-bot.service
sudo ss -lntp
curl --fail --silent https://juno.kim/api/v1/health/
sudo nginx -t
sudo journalctl -u juno-kim.service -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/juno-kim.error.log
```

Only `juno-kim.service` may be restarted for a website deployment. Never use
global process commands such as `pkill python`, `killall python`, or a blanket
`systemctl restart` on this shared instance.
