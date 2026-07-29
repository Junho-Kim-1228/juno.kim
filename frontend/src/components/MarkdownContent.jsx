import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { clampImageWidth, contentImagePresentation } from '../utils/markdownImages'

function ResizableMarkdownImage({ src, alt, width, onResize }) {
  const frameRef = useRef(null)
  const dragRef = useRef(null)
  const [previewWidth, setPreviewWidth] = useState(width)

  useEffect(() => setPreviewWidth(width), [width])

  const startResize = (event) => {
    const container = frameRef.current?.closest('.markdown-content')
    if (!container) return
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startWidth: previewWidth,
      containerWidth: container.clientWidth,
      latestWidth: previewWidth,
    }
  }

  const moveResize = (event) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    const nextWidth = clampImageWidth(drag.startWidth + ((event.clientX - drag.startX) / drag.containerWidth) * 100)
    drag.latestWidth = nextWidth
    setPreviewWidth(nextWidth)
  }

  const finishResize = (event) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    dragRef.current = null
    onResize(drag.latestWidth)
  }

  const resizeWithKeyboard = (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp'].includes(event.key)) return
    event.preventDefault()
    const direction = ['ArrowRight', 'ArrowUp'].includes(event.key) ? 5 : -5
    const nextWidth = clampImageWidth(previewWidth + direction)
    setPreviewWidth(nextWidth)
    onResize(nextWidth)
  }

  return <span ref={frameRef} className={`markdown-image-frame${onResize ? ' is-resizable' : ''}`} style={{ width: `${previewWidth}%` }}>
    <img src={src} alt={alt || ''} loading="lazy" />
    {onResize && <><span className="image-size-indicator">{previewWidth}%</span><button type="button" className="image-resize-handle" aria-label={`이미지 크기 조절, 현재 ${previewWidth}%`} onPointerDown={startResize} onPointerMove={moveResize} onPointerUp={finishResize} onPointerCancel={finishResize} onKeyDown={resizeWithKeyboard} /></>}
  </span>
}

export function MarkdownContent({ children, onImageResize }) {
  return <div className="prose markdown-content"><Markdown
    remarkPlugins={[remarkGfm]}
    skipHtml
    components={{
      a: ({ href, children: linkText }) => {
        const external = href?.startsWith('http://') || href?.startsWith('https://')
        return <a href={href} {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}>{linkText}</a>
      },
      img: ({ src, alt, node }) => {
        const presentation = contentImagePresentation(src)
        if (!presentation) return null
        return <ResizableMarkdownImage src={presentation.imageSrc} alt={alt} width={presentation.width} onResize={onImageResize ? (width) => onImageResize(src, width, node?.position) : null} />
      },
    }}
  >{children}</Markdown></div>
}
