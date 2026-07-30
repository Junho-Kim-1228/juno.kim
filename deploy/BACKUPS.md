# juno.kim backups

The production server creates an off-instance backup in a private Amazon S3 bucket every day at 03:30 Asia/Seoul. Each backup contains:

- `database.sql.gz`: MySQL data, including users, posts, comments, guestbook entries, and moderation state
- `media.tar.gz`: uploaded media files
- `git-revision.txt`: the application revision associated with the backup
- `SHA256SUMS`: integrity checksums for the backup files

S3 lifecycle management permanently expires backup objects after 30 days. The bucket blocks all public access and the EC2 instance role can upload only to the bucket's `backups/` prefix. It cannot read or delete existing backup objects.

Useful checks:

```bash
sudo systemctl status juno-kim-backup.timer
sudo systemctl list-timers juno-kim-backup.timer
sudo journalctl -u juno-kim-backup.service -n 50 --no-pager
```

Run a backup immediately:

```bash
sudo systemctl start juno-kim-backup.service
```

Restoration is intentionally manual because it overwrites production data. Before restoring, download the selected S3 backup through an authorized administrator session, verify `SHA256SUMS`, create a fresh safety backup, and stop only `juno-kim.service`. Restore the database and media together, then start the application and run its health checks. Never stop or restart `game-recruit-bot.service` during this process.
