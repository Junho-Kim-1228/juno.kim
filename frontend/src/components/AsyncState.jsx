export function LoadingState({ label = '불러오는 중입니다.' }) {
  return <p className="state-message">{label}</p>
}

export function ErrorState({ error }) {
  const data = error?.response?.data
  const message = error?.response?.status === 429
    ? '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'
    : data?.detail || (data && JSON.stringify(data)) || error?.message || '요청을 처리하지 못했습니다.'
  return <p className="state-message error" role="alert">{message}</p>
}
