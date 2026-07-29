import { useRef, useState } from 'react'

import { contentImageApi } from '../api/contentImages'

const allowedTypes = new Set(['image/jpeg', 'image/png', 'image/webp'])
const maxImageSize = 5 * 1024 * 1024

function imageErrorMessage(error) {
  const detail = error?.response?.data?.image
  if (Array.isArray(detail)) return detail[0]
  return detail || error?.response?.data?.detail || '이미지를 업로드하지 못했습니다.'
}

export function MarkdownEditor({ label, value, onChange, rows = 12, required = false }) {
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const valueRef = useRef(value)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  valueRef.current = value

  const uploadAndInsert = async (file, selectionStart, selectionEnd) => {
    if (!file || uploading) return
    if (!allowedTypes.has(file.type)) {
      setError('JPG, PNG, WebP 이미지만 올릴 수 있습니다.')
      return
    }
    if (file.size > maxImageSize) {
      setError('본문 이미지는 5MB 이하여야 합니다.')
      return
    }

    setUploading(true)
    setError(null)
    try {
      const uploaded = await contentImageApi.upload(file)
      const current = valueRef.current
      const start = Math.min(selectionStart, current.length)
      const end = Math.min(selectionEnd, current.length)
      const before = current.slice(0, start)
      const after = current.slice(end)
      const prefix = before && !before.endsWith('\n') ? '\n\n' : ''
      const suffix = after && !after.startsWith('\n') ? '\n\n' : ''
      const alt = file.name.replace(/\.[^.]+$/, '').replaceAll('[', '').replaceAll(']', '').trim() || '본문 이미지'
      const markdown = `${prefix}![${alt}](${uploaded.url})${suffix}`
      const nextValue = `${before}${markdown}${after}`
      const nextCursor = before.length + markdown.length
      onChange(nextValue)
      requestAnimationFrame(() => {
        textareaRef.current?.focus()
        textareaRef.current?.setSelectionRange(nextCursor, nextCursor)
      })
    } catch (uploadError) {
      setError(imageErrorMessage(uploadError))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const selection = () => ({
    start: textareaRef.current?.selectionStart ?? value.length,
    end: textareaRef.current?.selectionEnd ?? value.length,
  })

  const handleFile = (file) => {
    const { start, end } = selection()
    uploadAndInsert(file, start, end)
  }

  const handlePaste = (event) => {
    const file = Array.from(event.clipboardData?.files || []).find((item) => item.type.startsWith('image/'))
    if (!file) return
    event.preventDefault()
    handleFile(file)
  }

  const handleDrop = (event) => {
    const file = Array.from(event.dataTransfer?.files || []).find((item) => item.type.startsWith('image/'))
    if (!file) return
    event.preventDefault()
    handleFile(file)
  }

  return <div className="markdown-editor">
    <label>{label}<textarea ref={textareaRef} rows={rows} value={value} onChange={(event) => onChange(event.target.value)} onPaste={handlePaste} onDrop={handleDrop} required={required} /></label>
    <div className="markdown-toolbar">
      <button className="button-link secondary small" type="button" disabled={uploading} onClick={() => fileInputRef.current?.click()}>{uploading ? '업로드 중…' : '본문 이미지 추가'}</button>
      <span>커서 위치에 삽입됩니다. 붙여넣기와 드래그도 가능합니다.</span>
      <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(event) => handleFile(event.target.files[0])} />
    </div>
    {error && <p className="field-error" role="alert">{error}</p>}
  </div>
}
