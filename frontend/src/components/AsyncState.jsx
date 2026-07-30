export function LoadingState({ label = '불러오는 중입니다.' }) {
  return <p className="state-message">{label}</p>
}

const fieldLabels = {
  username: '아이디',
  email: '이메일',
  password: '비밀번호',
  password_confirm: '비밀번호 확인',
  current_password: '현재 비밀번호',
  new_password: '새 비밀번호',
  new_password_confirm: '새 비밀번호 확인',
}

function formatValidationError(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null

  const messages = Object.entries(data).flatMap(([field, value]) => {
    const label = fieldLabels[field] || field
    const values = Array.isArray(value) ? value : [value]
    return values.filter((message) => typeof message === 'string').map((message) => {
      const localizedMessage = message.replace(/\busername\b/gi, '아이디').replace(/\bemail\b/gi, '이메일')
      return localizedMessage.startsWith(label) ? localizedMessage : `${label}: ${localizedMessage}`
    })
  })

  return messages.length ? messages.join(' ') : null
}

export function ErrorState({ error }) {
  const data = error?.response?.data
  const message = error?.response?.status === 429
    ? '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'
    : data?.detail || formatValidationError(data) || error?.message || '요청을 처리하지 못했습니다.'
  return <p className="state-message error" role="alert">{message}</p>
}
