export function LoadingState({ label = '불러오는 중입니다.' }) {
  return <p className="state-message">{label}</p>
}

export function ErrorState({ error }) {
  const data = error?.response?.data
  const message = data?.detail || (data && JSON.stringify(data)) || error?.message || '요청을 처리하지 못했습니다.'
  return <p className="state-message error" role="alert">{message}</p>
}
