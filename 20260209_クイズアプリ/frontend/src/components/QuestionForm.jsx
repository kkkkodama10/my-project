import { useState } from 'react'
import { post, put } from '../api/client'

const EMPTY_CHOICE = (i) => ({ choice_index: i, text: '' })

const DEFAULT_FORM = {
  question_text: '',
  question_image: '',
  choices: [EMPTY_CHOICE(0), EMPTY_CHOICE(1), EMPTY_CHOICE(2), EMPTY_CHOICE(3)],
  correct_choice_index: 0,
  is_enabled: true,
}

export default function QuestionForm({ initial, onSaved, onCancel }) {
  const isEdit = !!initial

  const [form, setForm] = useState(() => {
    if (!initial) return DEFAULT_FORM
    return {
      question_text: initial.question_text || '',
      question_image: initial.question_image || '',
      choices: initial.choices.map(c => ({ ...c })),
      correct_choice_index: initial.correct_choice_index ?? 0,
      is_enabled: initial.is_enabled ?? true,
    }
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [imageUploading, setImageUploading] = useState(false)

  function setChoice(idx, value) {
    setForm(f => {
      const choices = f.choices.map((c, i) =>
        i === idx ? { ...c, text: value } : c
      )
      return { ...f, choices }
    })
  }

  async function handleImageUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setImageUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await post('/api/admin/assets/images', fd)
      if (!res.ok) throw new Error('upload failed')
      const data = await res.json()
      setForm(f => ({ ...f, question_image: data.url }))
    } catch (err) {
      setError('画像アップロード失敗: ' + err.message)
    } finally {
      setImageUploading(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const body = {
        question_text: form.question_text,
        question_image: form.question_image || null,
        choices: form.choices.map((c, i) => ({ choice_index: i, text: c.text })),
        correct_choice_index: Number(form.correct_choice_index),
        is_enabled: form.is_enabled,
      }
      const res = isEdit
        ? await put(`/api/admin/questions/${initial.question_id}`, body)
        : await post('/api/admin/questions', body)
      if (!res.ok) throw new Error(await res.text())
      const saved = await res.json()
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: '1px solid #ddd', padding: 12, borderRadius: 6, marginBottom: 12 }}>
      <h3 style={{ marginTop: 0 }}>{isEdit ? '問題を編集' : '新規問題'}</h3>

      <div style={{ marginBottom: 8 }}>
        <label>問題文</label><br />
        <textarea
          required
          rows={3}
          style={{ width: '100%', marginTop: 4 }}
          value={form.question_text}
          onChange={e => setForm(f => ({ ...f, question_text: e.target.value }))}
        />
      </div>

      <div style={{ marginBottom: 8 }}>
        <label>問題画像</label><br />
        {form.question_image && (
          <img src={form.question_image} alt="問題画像" style={{ maxHeight: 80, marginBottom: 4, display: 'block' }} />
        )}
        <input type="file" accept="image/*" onChange={handleImageUpload} disabled={imageUploading} />
        {imageUploading && <span> アップロード中...</span>}
      </div>

      <div style={{ marginBottom: 8 }}>
        <label>選択肢（正解: ラジオボタン選択）</label>
        {form.choices.map((c, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', marginTop: 4, gap: 8 }}>
            <input
              type="radio"
              name="correct"
              checked={Number(form.correct_choice_index) === i}
              onChange={() => setForm(f => ({ ...f, correct_choice_index: i }))}
            />
            <input
              type="text"
              required
              placeholder={`選択肢 ${i + 1}`}
              value={c.text}
              style={{ flex: 1 }}
              onChange={e => setChoice(i, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 8 }}>
        <label>
          <input
            type="checkbox"
            checked={form.is_enabled}
            onChange={e => setForm(f => ({ ...f, is_enabled: e.target.checked }))}
          />
          {' '}有効
        </label>
      </div>

      {error && <p style={{ color: 'red', margin: '4px 0' }}>{error}</p>}

      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit" disabled={saving}>{saving ? '保存中...' : '保存'}</button>
        {onCancel && <button type="button" onClick={onCancel}>キャンセル</button>}
      </div>
    </form>
  )
}
