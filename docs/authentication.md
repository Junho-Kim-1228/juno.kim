# 인증 및 토큰 저장 전략

## 선택한 방식

- Access Token: React 메모리에만 저장하고 API 요청의 `Authorization: Bearer <token>` 헤더로 전달합니다.
- Refresh Token: JavaScript에서 읽을 수 없는 HttpOnly 쿠키에만 저장합니다.
- 운영 쿠키: `Secure`, `HttpOnly`, `SameSite=Lax`를 적용하고 경로를 `/api/v1/auth/`로 제한합니다.
- Refresh Token을 사용할 때마다 회전시키고 이전 토큰을 blacklist에 등록합니다.

## localStorage를 사용하지 않는 이유

localStorage 값은 같은 Origin에서 실행된 JavaScript가 읽을 수 있습니다. XSS가 발생하면 수명이 긴 Refresh Token까지 탈취될 수 있으므로 장기 토큰 저장소로 사용하지 않습니다. Access Token은 짧은 수명으로 제한하고 새로고침 시 HttpOnly Refresh 쿠키를 이용해 다시 발급합니다.

HttpOnly 쿠키도 모든 공격을 막지는 않습니다. 브라우저는 쿠키를 자동 전송하므로 갱신과 로그아웃 요청은 허용된 Origin과 CSRF 정책을 함께 검사해야 합니다. 또한 XSS가 실행 중인 동안에는 메모리의 Access Token을 직접 읽지 못하더라도 사용자의 권한으로 요청을 보낼 수 있으므로 CSP, 출력 이스케이프, 의존성 관리가 계속 필요합니다.

## 토큰 수명

- Access Token: 15분
- Refresh Token: 7일
- Refresh Token 회전: 활성화
- 이전 Refresh Token blacklist: 활성화

운영 환경에서는 HTTPS가 확인된 뒤에만 인증 기능을 공개합니다.
