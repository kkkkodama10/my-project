import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listPersons, createPerson, deletePerson } from '../api/client'
import Toast from '../components/Toast'

export default function PersonListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleError = useCallback((e: unknown) => {
    setError(e instanceof Error ? e.message : String(e))
  }, [])

  const { data: persons = [], isLoading } = useQuery({
    queryKey: ['persons'],
    queryFn: listPersons,
  })

  const createMutation = useMutation({
    mutationFn: createPerson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      setName('')
    },
    onError: handleError,
  })

  const deleteMutation = useMutation({
    mutationFn: deletePerson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
    },
    onError: handleError,
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createMutation.mutate(trimmed)
  }

  return (
    <>
      {error && <Toast message={error} onClose={() => setError(null)} />}

      <h1 className="text-2xl font-bold text-gray-800 mb-6">人物一覧</h1>

      {/* 人物追加フォーム */}
      <form onSubmit={handleCreate} className="flex gap-2 mb-8">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="人物名を入力"
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          disabled={createMutation.isPending || !name.trim()}
          className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium"
        >
          追加
        </button>
      </form>

      {/* 人物カード一覧 */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : persons.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-12">
          人物が登録されていません
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {persons.map((person) => (
            <div
              key={person.id}
              className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm flex flex-col gap-2"
            >
              <button
                onClick={() => navigate(`/persons/${person.id}`)}
                className="text-left"
              >
                <p className="font-semibold text-gray-800 text-base">{person.name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {person.image_count} 枚の画像
                </p>
              </button>
              <div className="flex justify-end">
                <button
                  onClick={() => deleteMutation.mutate(person.id)}
                  disabled={deleteMutation.isPending}
                  className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                >
                  削除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
