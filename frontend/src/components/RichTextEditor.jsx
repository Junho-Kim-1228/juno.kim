import FileHandler from '@tiptap/extension-file-handler'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { Markdown } from '@tiptap/markdown'
import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { contentImageApi } from '../api/contentImages'
import { parseContentImageSource, serializeContentImageSource } from '../utils/contentImages'

const allowedImageTypes = ['image/jpeg', 'image/png', 'image/webp']
const maximumImageSize = 5 * 1024 * 1024

function cleanImageAlt(filename) {
  return filename.replace(/\.[^.]+$/, '').replaceAll('[', '').replaceAll(']', '').trim() || '본문 이미지'
}

function uploadErrorMessage(error) {
  const detail = error?.response?.data?.image
  if (Array.isArray(detail)) return detail[0]
  return detail || error?.response?.data?.detail || '이미지를 업로드하지 못했습니다.'
}

const ContentImage = Image.extend({
  parseHTML() {
    return [{
      tag: 'img[src]:not([src^="data:"])',
      getAttrs: (element) => {
        const image = parseContentImageSource(element.getAttribute('src'))
        if (!image) return false
        return {
          src: image.cleanSrc,
          alt: element.getAttribute('alt'),
          title: element.getAttribute('title'),
          width: image.pixelWidth,
          height: null,
        }
      },
    }]
  },
  parseMarkdown: (token, helpers) => {
    const image = parseContentImageSource(token.href)
    if (!image) return null
    return helpers.createNode('image', {
      src: image.cleanSrc,
      alt: token.text,
      title: token.title,
      width: image.pixelWidth,
      height: null,
    })
  },
  renderMarkdown: (node) => {
    const src = serializeContentImageSource(node.attrs?.src ?? '', node.attrs?.width)
    if (!src) return ''
    const alt = String(node.attrs?.alt ?? '').replaceAll('[', '').replaceAll(']', '')
    return `![${alt}](${src})`
  },
})

function ToolbarButton({ active = false, children, ...props }) {
  return <button type="button" className={`rich-text-tool${active ? ' active' : ''}`} {...props}>{children}</button>
}

function EditorToolbar({ editor, uploading, onImageClick }) {
  const state = useEditorState({
    editor,
    selector: ({ editor: currentEditor }) => currentEditor ? {
      bold: currentEditor.isActive('bold'),
      italic: currentEditor.isActive('italic'),
      underline: currentEditor.isActive('underline'),
      strike: currentEditor.isActive('strike'),
      bulletList: currentEditor.isActive('bulletList'),
      orderedList: currentEditor.isActive('orderedList'),
      blockquote: currentEditor.isActive('blockquote'),
      codeBlock: currentEditor.isActive('codeBlock'),
      link: currentEditor.isActive('link'),
      heading2: currentEditor.isActive('heading', { level: 2 }),
      heading3: currentEditor.isActive('heading', { level: 3 }),
      canUndo: currentEditor.can().chain().focus().undo().run(),
      canRedo: currentEditor.can().chain().focus().redo().run(),
    } : null,
  })

  if (!editor || !state) return null

  const setBlockType = (event) => {
    const type = event.target.value
    if (type === 'heading2') editor.chain().focus().toggleHeading({ level: 2 }).run()
    else if (type === 'heading3') editor.chain().focus().toggleHeading({ level: 3 }).run()
    else editor.chain().focus().setParagraph().run()
  }

  const setLink = () => {
    const previous = editor.getAttributes('link').href || ''
    const entered = window.prompt('링크 주소를 입력해 주세요.', previous)
    if (entered === null) return
    if (!entered.trim()) {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }
    const href = entered.startsWith('/') || /^[a-z]+:/i.test(entered) ? entered : `https://${entered}`
    editor.chain().focus().extendMarkRange('link').setLink({ href }).run()
  }

  const blockType = state.heading2 ? 'heading2' : state.heading3 ? 'heading3' : 'paragraph'

  return <div className="rich-text-toolbar" role="toolbar" aria-label="본문 서식">
    <select aria-label="문단 종류" value={blockType} onChange={setBlockType}><option value="paragraph">본문</option><option value="heading2">제목 2</option><option value="heading3">제목 3</option></select>
    <ToolbarButton active={state.bold} onClick={() => editor.chain().focus().toggleBold().run()}>굵게</ToolbarButton>
    <ToolbarButton active={state.italic} onClick={() => editor.chain().focus().toggleItalic().run()}>기울임</ToolbarButton>
    <ToolbarButton active={state.underline} onClick={() => editor.chain().focus().toggleUnderline().run()}>밑줄</ToolbarButton>
    <ToolbarButton active={state.strike} onClick={() => editor.chain().focus().toggleStrike().run()}>취소선</ToolbarButton>
    <ToolbarButton active={state.bulletList} onClick={() => editor.chain().focus().toggleBulletList().run()}>목록</ToolbarButton>
    <ToolbarButton active={state.orderedList} onClick={() => editor.chain().focus().toggleOrderedList().run()}>번호</ToolbarButton>
    <ToolbarButton active={state.blockquote} onClick={() => editor.chain().focus().toggleBlockquote().run()}>인용</ToolbarButton>
    <ToolbarButton active={state.codeBlock} onClick={() => editor.chain().focus().toggleCodeBlock().run()}>코드</ToolbarButton>
    <ToolbarButton active={state.link} onClick={setLink}>링크</ToolbarButton>
    <ToolbarButton disabled={uploading} onClick={onImageClick}>{uploading ? '업로드 중…' : '이미지'}</ToolbarButton>
    <span className="rich-text-toolbar-spacer" />
    <ToolbarButton disabled={!state.canUndo} onClick={() => editor.chain().focus().undo().run()}>실행 취소</ToolbarButton>
    <ToolbarButton disabled={!state.canRedo} onClick={() => editor.chain().focus().redo().run()}>다시 실행</ToolbarButton>
  </div>
}

export function RichTextEditor({ label, value, onChange, minimumHeight = 320 }) {
  const fileInputRef = useRef(null)
  const onChangeRef = useRef(onChange)
  const lastSyncedValueRef = useRef(value || '')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => { onChangeRef.current = onChange }, [onChange])

  const uploadImages = useCallback(async (currentEditor, files, dropPosition) => {
    const images = Array.from(files).filter((file) => allowedImageTypes.includes(file.type))
    if (!images.length) {
      setError('JPG, PNG, WebP 이미지만 올릴 수 있습니다.')
      return
    }
    const oversized = images.find((file) => file.size > maximumImageSize)
    if (oversized) {
      setError('본문 이미지는 5MB 이하여야 합니다.')
      return
    }

    setUploading(true)
    setError(null)
    try {
      let insertionPosition = Number.isInteger(dropPosition) ? dropPosition : null
      for (const file of images) {
        const uploaded = await contentImageApi.upload(file)
        const imageNode = { type: 'image', attrs: { src: uploaded.url, alt: cleanImageAlt(file.name) } }
        if (insertionPosition !== null) {
          currentEditor.chain().focus().insertContentAt(insertionPosition, imageNode).run()
          insertionPosition += 1
        } else {
          currentEditor.chain().focus().setImage(imageNode.attrs).run()
        }
      }
    } catch (uploadError) {
      setError(uploadErrorMessage(uploadError))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }, [])

  const extensions = useMemo(() => [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      link: { openOnClick: false, autolink: true, linkOnPaste: true, defaultProtocol: 'https' },
    }),
    ContentImage.configure({
      allowBase64: false,
      resize: {
        enabled: true,
        directions: ['bottom-right'],
        minWidth: 80,
        minHeight: 50,
        alwaysPreserveAspectRatio: true,
      },
    }),
    Placeholder.configure({ placeholder: '내용을 입력해 주세요.' }),
    FileHandler.configure({
      allowedMimeTypes: allowedImageTypes,
      consumePasteEvent: true,
      onPaste: (currentEditor, files) => { void uploadImages(currentEditor, files) },
      onDrop: (currentEditor, files, position) => { void uploadImages(currentEditor, files, position) },
    }),
    Markdown.configure({ markedOptions: { gfm: true, breaks: true } }),
  ], [uploadImages])

  const editor = useEditor({
    extensions,
    content: '',
    contentType: 'markdown',
    editorProps: { attributes: { class: 'rich-text-body' } },
    onUpdate: ({ editor: currentEditor }) => {
      const markdown = currentEditor.getMarkdown()
      lastSyncedValueRef.current = markdown
      onChangeRef.current(markdown)
    },
  }, [extensions])

  useEffect(() => {
    if (!editor || value === lastSyncedValueRef.current) return
    editor.commands.setContent(value || '', { contentType: 'markdown', emitUpdate: false })
    lastSyncedValueRef.current = value || ''
  }, [editor, value])

  return <div className="rich-text-field">
    <span className="rich-text-label">{label}</span>
    <div className="rich-text-editor" style={{ '--rich-text-min-height': `${minimumHeight}px` }}>
      <EditorToolbar editor={editor} uploading={uploading} onImageClick={() => fileInputRef.current?.click()} />
      <EditorContent editor={editor} />
      <input ref={fileInputRef} type="file" accept={allowedImageTypes.join(',')} multiple hidden onChange={(event) => { if (editor) void uploadImages(editor, event.target.files) }} />
    </div>
    <small className="form-note">본문에서 바로 편집할 수 있습니다. 이미지는 붙여넣거나 드래그한 뒤 오른쪽 아래 손잡이로 크기를 조절하세요.</small>
    {error && <p className="field-error" role="alert">{error}</p>}
  </div>
}
