import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { parseContentImageSource } from '../utils/contentImages'

export function MarkdownContent({ children }) {
  return <div className="prose markdown-content"><Markdown
    remarkPlugins={[remarkGfm]}
    skipHtml
    components={{
      a: ({ href, children: linkText }) => {
        const external = href?.startsWith('http://') || href?.startsWith('https://')
        return <a href={href} {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}>{linkText}</a>
      },
      img: ({ src, alt }) => {
        const image = parseContentImageSource(src)
        if (!image) return null
        return <span className="markdown-image-frame" style={{ width: image.displayWidth }}><img src={image.cleanSrc} alt={alt || ''} loading="lazy" /></span>
      },
    }}
  >{children}</Markdown></div>
}
