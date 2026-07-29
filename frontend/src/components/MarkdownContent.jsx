import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function isAllowedContentImage(src) {
  if (!src) return false
  try {
    const url = new URL(src, window.location.origin)
    return url.origin === window.location.origin && url.pathname.startsWith('/media/content/')
  } catch {
    return false
  }
}

export function MarkdownContent({ children }) {
  return <div className="prose markdown-content"><Markdown
    remarkPlugins={[remarkGfm]}
    skipHtml
    components={{
      a: ({ href, children: linkText }) => {
        const external = href?.startsWith('http://') || href?.startsWith('https://')
        return <a href={href} {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}>{linkText}</a>
      },
      img: ({ src, alt }) => isAllowedContentImage(src) ? <img src={src} alt={alt || ''} loading="lazy" /> : null,
    }}
  >{children}</Markdown></div>
}
