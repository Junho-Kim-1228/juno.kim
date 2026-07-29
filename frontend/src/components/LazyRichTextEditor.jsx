import { lazy, Suspense } from 'react'

const RichTextEditor = lazy(() => import('./RichTextEditor').then((module) => ({ default: module.RichTextEditor })))

export function LazyRichTextEditor(props) {
  return <Suspense fallback={<p className="rich-text-loading">편집기를 불러오는 중입니다.</p>}><RichTextEditor {...props} /></Suspense>
}
