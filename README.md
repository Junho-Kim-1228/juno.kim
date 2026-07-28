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

