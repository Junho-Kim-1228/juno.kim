const minimumImageWidth = 20
const maximumImageWidth = 100

export function clampImageWidth(width) {
  return Math.min(maximumImageWidth, Math.max(minimumImageWidth, Math.round(width)))
}

export function contentImagePresentation(src) {
  if (!src) return null
  try {
    const url = new URL(src, window.location.origin)
    if (url.origin !== window.location.origin || !url.pathname.startsWith('/media/content/')) return null
    const widthMatch = url.hash.match(/^#width=(\d{1,3})$/)
    const width = widthMatch ? clampImageWidth(Number(widthMatch[1])) : maximumImageWidth
    url.hash = ''
    const imageSrc = src.startsWith('/') ? `${url.pathname}${url.search}` : url.href
    return { imageSrc, width }
  } catch {
    return null
  }
}

function sourceWithWidth(src, width) {
  return `${src.replace(/#width=\d{1,3}$/, '').split('#')[0]}#width=${clampImageWidth(width)}`
}

export function resizeMarkdownImage(markdown, src, width, position) {
  const nextSrc = sourceWithWidth(src, width)
  const replaceSource = (source) => source.replace(`(${src})`, `(${nextSrc})`)
  const start = position?.start?.offset
  const end = position?.end?.offset

  if (Number.isInteger(start) && Number.isInteger(end)) {
    const imageMarkdown = markdown.slice(start, end)
    const resizedImageMarkdown = replaceSource(imageMarkdown)
    if (imageMarkdown !== resizedImageMarkdown) {
      return `${markdown.slice(0, start)}${resizedImageMarkdown}${markdown.slice(end)}`
    }
  }
  return replaceSource(markdown)
}
