const minimumPixelWidth = 80
const maximumPixelWidth = 1600
const legacyEditorWidth = 650

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, Math.round(value)))
}

export function parseContentImageSource(src) {
  if (!src) return null
  try {
    const url = new URL(src, window.location.origin)
    if (url.origin !== window.location.origin || !url.pathname.startsWith('/media/content/')) return null

    const pixelMatch = url.hash.match(/^#width=(\d{2,4})px$/)
    const percentMatch = url.hash.match(/^#width=(\d{1,3})$/)
    const pixelWidth = pixelMatch
      ? clamp(Number(pixelMatch[1]), minimumPixelWidth, maximumPixelWidth)
      : percentMatch
        ? Math.round(legacyEditorWidth * clamp(Number(percentMatch[1]), 20, 100) / 100)
        : null
    const displayWidth = pixelMatch
      ? `${pixelWidth}px`
      : percentMatch
        ? `${clamp(Number(percentMatch[1]), 20, 100)}%`
        : '100%'

    url.hash = ''
    const cleanSrc = src.startsWith('/') ? `${url.pathname}${url.search}` : url.href
    return { cleanSrc, pixelWidth, displayWidth }
  } catch {
    return null
  }
}

export function serializeContentImageSource(src, width) {
  const image = parseContentImageSource(src)
  if (!image) return ''
  if (!width) return image.cleanSrc
  return `${image.cleanSrc}#width=${clamp(width, minimumPixelWidth, maximumPixelWidth)}px`
}
