# juno.kim

EC2 + Nginx + Gunicorn + Django 구조를 전제로 한 개인 사이트입니다.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Production shape

- DNS: `juno.kim` -> EC2 public IP
- Nginx: `deploy/nginx/juno.kim.conf`
- Gunicorn systemd: `deploy/systemd/gunicorn.service`
- Django entrypoint: `config.wsgi:application`

## Notes

- 기본 개발 DB는 SQLite입니다.
- 운영 DB는 `DATABASE_URL` 환경 변수로 교체할 수 있습니다.
- 정적 파일은 `python manage.py collectstatic` 후 Nginx가 직접 서빙합니다.
