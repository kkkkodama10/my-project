import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listComparisons, listPersons } from '../api/client'

export default function HistoryPage() {
  const { data: comparisons = [], isLoading: comparisonsLoading } = useQuery({
    queryKey: ['comparisons'],
    queryFn: listComparisons,
  })

  const { data: persons = [] } = useQuery({
    queryKey: ['persons'],
    queryFn: listPersons,
  })

  const personMap = Object.fromEntries(persons.map((p) => [p.id, p.name]))

  return (
    <>
      <div className="mb-6">
        <Link to="/compare" className="text-sm text-blue-500 hover:underline">
          ← 比較ページへ戻る
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-800 mb-6">比較履歴</h1>

      {comparisonsLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : comparisons.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-12">
          比較履歴がありません
        </p>
      ) : (
        <div className="space-y-3">
          {comparisons.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-gray-200 rounded-lg px-5 py-4 shadow-sm flex items-center justify-between"
            >
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {personMap[item.person_a_id] ?? item.person_a_id}
                  <span className="text-gray-400 mx-2">vs</span>
                  {personMap[item.person_b_id] ?? item.person_b_id}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(item.created_at).toLocaleString('ja-JP')}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-blue-600">
                  {item.score.toFixed(1)}%
                </p>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    item.is_valid
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {item.is_valid ? '有効' : '無効'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
