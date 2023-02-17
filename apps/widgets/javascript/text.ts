import * as Quill from 'quill'

const toolbarOptions = [
  [{ header: [1, 2, 3, false] }],
  [{ size: ['small', false, 'large', 'huge'] }],
  ['bold', 'italic', 'underline', 'strike', 'link'],
  [{ align: [] }],
  [{ list: 'ordered' }, { list: 'bullet' }],
  ['clean'],
]

const quill = ($el, readOnly: boolean) => {
  const editor = new Quill($el, {
    placeholder: 'Type your notes here...',
    theme: 'snow',
    readOnly: readOnly,
    bounds: $el,
    modules: {
      toolbar: readOnly ? '' : toolbarOptions,
    },
  })

  return editor
}

export const Text = { quill }
