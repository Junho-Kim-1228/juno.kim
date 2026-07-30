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
  display_name: '표시 이름',
  first_name: '이름',
  last_name: '성',
  bio: '소개',
  avatar: '프로필 이미지',
  website_url: '웹사이트',
  github_url: 'GitHub',
  title: '제목',
  name: '이름',
  summary: '한 줄 소개',
  description: '설명',
  excerpt: '요약',
  content: '내용',
  message: '메시지',
  staff_reply: '답글',
  parent: '댓글',
  post_slug: '게시글',
  category_id: '카테고리',
  tag_ids: '태그',
  kind: '분류',
  status: '공개 상태',
  is_featured: '공지 설정',
  remove_cover_image: '대표 이미지',
  ordering: '정렬 순서',
  technologies: '기술 스택',
  repository_url: '저장소 주소',
  live_url: '서비스 주소',
  thumbnail: '썸네일',
  cover_image: '대표 이미지',
  image: '이미지',
  started_on: '시작일',
  ended_on: '종료일',
  reason: '신고 사유',
  token: '인증 링크',
  non_field_errors: '',
  detail: '',
}

const knownMessages = {
  'An account with this email already exists.': '이미 사용 중인 이메일입니다.',
  'This field may not be blank.': '입력해 주세요.',
  'This field is required.': '필수 입력 항목입니다.',
  'Enter a valid email address.': '올바른 이메일 주소를 입력해 주세요.',
  'Enter a valid URL.': '올바른 웹 주소를 입력해 주세요.',
}

function localizeMessage(message) {
  const trimmed = message.trim()
  if (knownMessages[trimmed]) return knownMessages[trimmed]
  return trimmed
    .replace(/^username(?=은|는|이|가)/i, '아이디')
    .replace(/^email(?=은|는|이|가)/i, '이메일')
    .replace(/^display_name(?=은|는|이|가)/i, '표시 이름')
}

function formatValidationError(data) {
  if (typeof data === 'string') return localizeMessage(data)
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null

  const messages = Object.entries(data).flatMap(([field, value]) => {
    const label = fieldLabels[field] ?? '입력값'
    const values = Array.isArray(value) ? value : [value]
    return values.filter((message) => typeof message === 'string').map((message) => {
      const localizedMessage = localizeMessage(message)
      return !label || localizedMessage.startsWith(label) ? localizedMessage : `${label}: ${localizedMessage}`
    })
  })

  return messages.length ? messages.join(' · ') : null
}

export function ErrorState({ error }) {
  const data = error?.response?.data
  const message = error?.response?.status === 429
    ? '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'
    : formatValidationError(data) || error?.message || '요청을 처리하지 못했습니다.'
  return <p className="state-message error" role="alert">{message}</p>
}
