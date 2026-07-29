# juno.kim logging and monitoring

The production application writes Django and Gunicorn logs to the systemd journal. Nginx keeps its normal access and error logs under `/var/log/nginx`; the operating system's Nginx logrotate policy rotates those files.

Useful commands:

```bash
sudo journalctl -u juno-kim.service --since today --no-pager
sudo journalctl -u juno-kim-monitor.service -n 50 --no-pager
sudo systemctl status juno-kim-monitor.timer
sudo tail -n 100 /var/log/nginx/juno-kim.error.log
```

The local timer checks the application service, database-backed health endpoint, `/var` disk usage, and available memory every five minutes. The GitHub Actions workflow checks the public homepage, public health endpoint, and TLS certificate every fifteen minutes. It opens one GitHub issue while an incident is active and closes it after recovery.

No email address, verification token, password, cookie, or authorization value should be intentionally logged. `SensitiveDataFilter` provides a final redaction layer, but application log statements must still use internal numeric IDs instead of personal data.
