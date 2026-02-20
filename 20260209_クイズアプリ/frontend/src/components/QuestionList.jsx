import { put } from '../api/client'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function SortableRow({ question, onEdit, onToggleEnabled }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: question.question_id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
    padding: '8px 4px',
    borderBottom: '1px solid #eee',
    background: '#fff',
  }

  return (
    <div ref={setNodeRef} style={style}>
      {/* ドラッグハンドル */}
      <span
        {...attributes}
        {...listeners}
        style={{ cursor: 'grab', color: '#999', userSelect: 'none', paddingTop: 2 }}
        title="ドラッグして並び替え"
      >
        ⠿
      </span>

      <div style={{ flex: 1 }}>
        <strong>{question.question_text}</strong>
        <div style={{ fontSize: '0.85em', color: '#666', marginTop: 2 }}>
          {question.choices.map(c => (
            <span
              key={c.choice_index}
              style={{
                marginRight: 6,
                color: c.choice_index === question.correct_choice_index ? '#22863a' : undefined,
                fontWeight: c.choice_index === question.correct_choice_index ? 600 : undefined,
              }}
            >
              {c.text}
            </span>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <label style={{ fontSize: '0.85em' }}>
          <input
            type="checkbox"
            checked={question.is_enabled}
            onChange={() => onToggleEnabled(question)}
          />
          {' '}有効
        </label>
        <button onClick={() => onEdit(question)} style={{ fontSize: '0.85em' }}>
          編集
        </button>
      </div>
    </div>
  )
}

export default function QuestionList({ questions, onQuestionsChange, onEdit }) {
  const sensors = useSensors(useSensor(PointerSensor))

  async function handleDragEnd(event) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = questions.findIndex(q => q.question_id === active.id)
    const newIndex = questions.findIndex(q => q.question_id === over.id)
    const reordered = arrayMove(questions, oldIndex, newIndex)
    onQuestionsChange(reordered)

    try {
      await put('/api/admin/questions/reorder', {
        ordered_ids: reordered.map(q => q.question_id),
      })
    } catch (e) {
      console.error('reorder failed', e)
    }
  }

  async function handleToggleEnabled(question) {
    try {
      const res = await put(`/api/admin/questions/${question.question_id}/enabled`, {
        enabled: !question.is_enabled,
      })
      if (!res.ok) return
      const updated = await res.json()
      onQuestionsChange(questions.map(q =>
        q.question_id === updated.question_id ? updated : q
      ))
    } catch (e) {
      console.error('toggle enabled failed', e)
    }
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext
        items={questions.map(q => q.question_id)}
        strategy={verticalListSortingStrategy}
      >
        {questions.map(q => (
          <SortableRow
            key={q.question_id}
            question={q}
            onEdit={onEdit}
            onToggleEnabled={handleToggleEnabled}
          />
        ))}
      </SortableContext>
    </DndContext>
  )
}
