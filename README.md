# juno.kim

개인 포트폴리오, 프로젝트 아카이브, 기술 블로그를 위한 풀스택 웹 애플리케이션입니다.

## 기술 스택

- Frontend: React, Vite, React Router, Axios
- Backend: Python, Django, Django REST Framework
- Database: MySQL
- Web/WSGI: Nginx, Gunicorn
- Deployment: AWS EC2 Ubuntu, systemd, Certbot

## 디렉터리 구조

```text
juno.kim/
├── backend/          # Django API와 관리자 페이지
├── frontend/         # React SPA
├── deploy/
│   ├── nginx/        # 사이트별 Nginx 설정
│   ├── systemd/      # juno-kim.service
│   └── scripts/      # 배포 및 롤백 스크립트
└── docs/             # 운영 및 개발 문서
```

## 개발 환경

- Python 3.14+
- Node.js 24+
- npm 11+
- Git 2.45+
- MySQL 8 계열

세부 설치 및 실행 방법은 각 구현 단계가 안정화되면서 이 문서에 추가합니다.

### 로컬 MySQL

로컬 데이터베이스는 Docker의 MySQL 8.4 컨테이너를 사용합니다. 호스트의 3306 포트와 충돌하거나 Windows에서 바인딩이 제한되는 환경을 고려해 `127.0.0.1:3307`에만 공개합니다. 컨테이너 내부에서는 기본 MySQL 포트 3306을 사용합니다.

```powershell
Copy-Item backend/.env.example backend/.env
# backend/.env의 빈 개발 환경변수를 안전한 로컬 값으로 채운 뒤 실행합니다.
docker compose --env-file backend/.env -f deploy/docker-compose.local.yml up -d mysql
docker compose --env-file backend/.env -f deploy/docker-compose.local.yml ps
```

Django migration:

```powershell
backend/.venv/Scripts/python.exe backend/manage.py migrate
```

### 백엔드 테스트

자동화 테스트는 개발 MySQL 데이터를 변경하지 않고 메모리 SQLite를 사용합니다.

```powershell
Set-Location backend
$env:TEST_DATABASE_URL = 'sqlite:///:memory:'
.\.venv\Scripts\python.exe .\manage.py test apps
Remove-Item Env:TEST_DATABASE_URL
```

## 환경변수와 보안

- 실제 환경변수 파일과 비밀값은 Git에 커밋하지 않습니다.
- 저장소에는 변수 이름과 설명만 담은 `.env.example`만 포함합니다.
- 운영 환경에서는 `DEBUG=False`, HTTPS, Secure Cookie를 사용합니다.
- MySQL과 Gunicorn은 외부 인터넷에 직접 노출하지 않습니다.

## AWS 운영 원칙

이 웹사이트는 동일한 EC2에서 실행 중인 Discord Bot과 완전히 분리합니다.

- 별도의 배포 디렉터리와 Python 가상환경 사용
- 별도의 `juno-kim.service`만 생성 및 재시작
- 기존 Discord Bot 파일, 환경변수, 프로세스, 포트 및 systemd 설정 변경 금지
- 외부 공개 포트는 Nginx의 80/443으로 제한

## 현재 상태

프로젝트 기반 구조를 구성하는 중입니다.
